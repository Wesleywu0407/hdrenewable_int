"""Dashboard utility helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


def render_html(html: str) -> None:
    """Render raw HTML across Streamlit versions."""
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def format_refresh_time(value: str | None) -> str:
    if not value:
        return "Not available"
    try:
        parsed = datetime.fromisoformat(value)
        local_time = parsed.astimezone()
    except ValueError:
        return value
    return local_time.strftime("%d %b %Y · %H:%M")


def parse_refresh_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def format_run_duration(start_time: datetime | None, end_time: datetime | None) -> str:
    if not start_time or not end_time:
        return "n/a"
    seconds = max(0, int((end_time - start_time).total_seconds()))
    if seconds < 60:
        return f"{seconds}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    return f"{minutes}m {remaining_seconds}s"


def is_refresh_stale(value: str | None) -> bool:
    parsed_time = parse_refresh_datetime(value)
    if not parsed_time:
        return False
    now = datetime.now(parsed_time.tzinfo).astimezone(parsed_time.tzinfo) if parsed_time.tzinfo else datetime.now()
    return (now - parsed_time).total_seconds() > 24 * 60 * 60


def simplify_refresh_error(error_text: str) -> str:
    if "HTTP Error 403: Forbidden" in error_text:
        return "403 Forbidden"
    if "HTTP Error 404: Not Found" in error_text:
        return "404 Not Found"
    if "The read operation timed out" in error_text:
        return "Read timeout"
    if "Connection refused" in error_text:
        return "Connection refused"
    return error_text[:30]


def parse_refresh_log(raw_log: str) -> dict[str, Any]:
    """Parse the dashboard refresh log format into structured fields."""
    parsed: dict[str, Any] = {"sources": [], "files": []}
    current_list: str | None = None
    for raw_line in raw_log.splitlines():
        line = raw_line.strip()
        if not line:
            current_list = None
            continue
        if line.endswith(":"):
            current_list = line[:-1]
            continue
        if line.startswith("start_time:"):
            parsed["start_time"] = line.split(":", 1)[1].strip()
        elif line.startswith("end_time:"):
            parsed["end_time"] = line.split(":", 1)[1].strip()
        elif line.startswith("news_items_collected:"):
            parsed["items"] = line.split(":", 1)[1].strip()
        elif line.startswith("error:"):
            parsed["error"] = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            parsed["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("- ") and current_list == "sources_attempted":
            source_line = line[2:]
            source_name, _, detail = source_line.partition(": ")
            items_text, _, error_text = detail.partition(" | error: ")
            item_count = items_text.split(" ", 1)[0] if items_text else "0"
            parsed["sources"].append(
                {
                    "name": source_name,
                    "items": item_count,
                    "error": error_text.strip() or None,
                }
            )
        elif line.startswith("- ") and current_list in {"files_written", "expected_outputs"}:
            parsed["files"].append(line[2:])
    return parsed
