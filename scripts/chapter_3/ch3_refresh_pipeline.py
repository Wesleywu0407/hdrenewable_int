"""Isolated Chapter 3 policy/news refresh pipeline.

This backend-only script prepares refresh artifacts for Chapter 3 without
touching dashboard files, raw data, generated figures, or other scripts.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime" / "ch3"
LOG_DIR = PROJECT_ROOT / "logs"

NEWS_PATH = RUNTIME_DIR / "latest_policy_news.json"
STATUS_PATH = RUNTIME_DIR / "last_run_status.json"
LOG_PATH = LOG_DIR / "ch3_refresh_log.txt"

FILES_UPDATED = [
    "runtime/ch3/latest_policy_news.json",
    "runtime/ch3/last_run_status.json",
    "logs/ch3_refresh_log.txt",
]

HTTP_TIMEOUT_SECONDS = 15
MAX_ITEMS = 8
SOURCE_CONFIGS = [
    {
        "name": "AEMO Newsroom",
        "url": "https://aemo.com.au/newsroom/news-updates",
        "tag": "Grid Planning",
    },
    {
        "name": "Australian Energy Regulator News",
        "url": "https://www.aer.gov.au/news/articles",
        "tag": "Policy Update",
    },
    {
        "name": "Australian Government Energy News",
        "url": "https://www.energy.gov.au/news-media/news",
        "tag": "Policy Update",
    },
    {
        "name": "Clean Energy Council News",
        "url": "https://cleanenergycouncil.org.au/news-resources",
        "tag": "Market Opportunity",
        "path_prefix": "/news-resources/",
    },
]

RELEVANCE_KEYWORDS = (
    "aemo",
    "nem",
    "energy",
    "electricity",
    "renewable",
    "renewables",
    "grid",
    "transmission",
    "storage",
    "battery",
    "batteries",
    "capacity",
    "data centre",
    "data center",
    "demand",
    "policy",
    "market",
)


def iso_now() -> str:
    return datetime.now(UTC).isoformat()


def ensure_safe_output_path(path: Path, root: Path) -> None:
    output_root = root.resolve()
    target = path.resolve()
    if output_root not in (target, *target.parents):
        raise ValueError(f"Refusing to write outside {root}: {path}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_safe_output_path(path, RUNTIME_DIR)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_log(
    *,
    start_time: str,
    end_time: str,
    items_scraped: int,
    files_written: list[str],
    source_results: list[dict[str, Any]],
    error: str | None,
) -> None:
    ensure_safe_output_path(LOG_PATH, LOG_DIR)
    log_lines = [
        "Chapter 3 refresh pipeline run",
        f"start_time: {start_time}",
        "sources_attempted:",
        *(
            f"- {result['source']}: {result['items_collected']} items"
            + (f" | error: {result['error']}" if result.get("error") else "")
            for result in source_results
        ),
        f"end_time: {end_time}",
        "files_written:",
        *(f"- {file_path}" for file_path in files_written),
        f"news_items_collected: {items_scraped}",
        f"error: {error}" if error else "error: none",
        "",
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")


def clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def title_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    slug = html.unescape(slug)
    slug = re.sub(r"[-_]+", " ", slug)
    slug = re.sub(r"\s+", " ", slug)
    return slug.strip().title()


def normalize_timestamp(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()
    except (TypeError, ValueError):
        return clean_text(value)


def is_relevant(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in RELEVANCE_KEYWORDS)


def fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "HDRE-Chapter3-Refresh/1.0 (+https://aemo.com.au)",
            "Accept": "application/rss+xml, application/atom+xml, text/html, */*",
        },
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def item_tag(title: str, default_tag: str) -> str:
    lowered = title.lower()
    if "data centre" in lowered or "data center" in lowered or "demand" in lowered:
        return "Data Centre Demand"
    if "battery" in lowered or "batteries" in lowered or "storage" in lowered:
        return "Storage"
    if "aemo" in lowered or "nem" in lowered or "grid" in lowered or "transmission" in lowered:
        return "Grid Planning"
    if "renewable" in lowered or "market" in lowered or "investment" in lowered:
        return "Market Opportunity"
    return default_tag


def parse_feed_items(source: dict[str, str], source_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(source_text)
    channel_items = root.findall(".//item")
    atom_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    parsed_items: list[dict[str, str]] = []

    for node in channel_items:
        title = clean_text(node.findtext("title") or "")
        if not title or not is_relevant(title):
            continue
        summary = clean_text(node.findtext("description") or node.findtext("summary") or title)
        link = clean_text(node.findtext("link") or source["url"])
        timestamp = normalize_timestamp(node.findtext("pubDate") or node.findtext("date"))
        parsed_items.append(
            {
                "title": title,
                "summary": summary[:280],
                "source": source["name"],
                "timestamp": timestamp,
                "tag": item_tag(title, source["tag"]),
                "url": link,
            }
        )

    for node in atom_items:
        title = clean_text(node.findtext("{http://www.w3.org/2005/Atom}title") or "")
        if not title or not is_relevant(title):
            continue
        summary = clean_text(
            node.findtext("{http://www.w3.org/2005/Atom}summary")
            or node.findtext("{http://www.w3.org/2005/Atom}content")
            or title
        )
        link = source["url"]
        for link_node in node.findall("{http://www.w3.org/2005/Atom}link"):
            href = link_node.attrib.get("href")
            if href:
                link = urljoin(source["url"], href)
                break
        timestamp = normalize_timestamp(
            node.findtext("{http://www.w3.org/2005/Atom}updated")
            or node.findtext("{http://www.w3.org/2005/Atom}published")
        )
        parsed_items.append(
            {
                "title": title,
                "summary": summary[:280],
                "source": source["name"],
                "timestamp": timestamp,
                "tag": item_tag(title, source["tag"]),
                "url": link,
            }
        )

    return parsed_items


def parse_html_items(source: dict[str, str], source_text: str) -> list[dict[str, str]]:
    document = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", source_text, flags=re.I | re.S)
    link_matches = re.findall(
        r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        document,
        flags=re.I | re.S,
    )
    items: list[dict[str, str]] = []

    for href, label_html in link_matches:
        url = urljoin(source["url"], html.unescape(href))
        parsed_url = urlparse(url)
        path_prefix = source.get("path_prefix")
        if (
            url.startswith("mailto:")
            or url.startswith("tel:")
            or parsed_url.fragment
            or (path_prefix and not parsed_url.path.startswith(path_prefix))
            or parsed_url.path.rstrip("/") == urlparse(source["url"]).path.rstrip("/")
        ):
            continue
        title = clean_text(label_html)
        if title.lower() in {"find out more", "read more", "learn more", "view more"}:
            title = title_from_url(url)
        if len(title) < 18 or not is_relevant(title):
            continue
        items.append(
            {
                "title": title,
                "summary": title,
                "source": source["name"],
                "timestamp": "",
                "tag": item_tag(title, source["tag"]),
                "url": url,
            }
        )

    return items


def collect_source_items(source: dict[str, str]) -> tuple[list[dict[str, str]], str | None]:
    try:
        source_text = fetch_text(source["url"])
        try:
            items = parse_feed_items(source, source_text)
        except ET.ParseError:
            items = parse_html_items(source, source_text)
        return items, None
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
        return [], str(exc)


def dedupe_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for item in items:
        key = item["url"].strip().lower() or item["title"].strip().lower()
        if not item["title"] or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def collect_policy_news() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    collected_items: list[dict[str, str]] = []
    source_results: list[dict[str, Any]] = []

    for source in SOURCE_CONFIGS:
        items, error = collect_source_items(source)
        relevant_items = dedupe_items(items)
        collected_items.extend(relevant_items)
        source_results.append(
            {
                "source": source["name"],
                "url": source["url"],
                "items_collected": len(relevant_items),
                "error": error,
            }
        )

    final_items = dedupe_items(collected_items)[:MAX_ITEMS]
    return {
        "last_updated": iso_now(),
        "source_mode": "live_configured_sources",
        "items": final_items,
    }, source_results


def run() -> int:
    start_time = iso_now()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    source_results: list[dict[str, Any]] = []

    try:
        news_payload, source_results = collect_policy_news()
        write_json(NEWS_PATH, news_payload)

        end_time = iso_now()
        items_scraped = len(news_payload["items"])
        status_payload = {
            "status": "success",
            "last_updated": end_time,
            "items_scraped": items_scraped,
            "files_updated": FILES_UPDATED,
            "last_error": None,
        }
        write_json(STATUS_PATH, status_payload)
        write_log(
            start_time=start_time,
            end_time=end_time,
            items_scraped=items_scraped,
            files_written=FILES_UPDATED,
            source_results=source_results,
            error=None,
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - failure must be captured in status.
        end_time = iso_now()
        error_message = str(exc)
        status_payload = {
            "status": "failed",
            "last_updated": end_time,
            "items_scraped": 0,
            "files_updated": FILES_UPDATED,
            "last_error": error_message,
        }
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        write_json(STATUS_PATH, status_payload)
        write_log(
            start_time=start_time,
            end_time=end_time,
            items_scraped=0,
            files_written=FILES_UPDATED,
            source_results=source_results,
            error=error_message,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
