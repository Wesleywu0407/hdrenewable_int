"""Shared cache, API, and logging helpers for data ingestion scripts."""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Callable, Iterable
from pathlib import Path

import pandas as pd

from .constants import CACHE_MAX_AGE_H

LOGGER_NAME = "hdre.pipeline"
type PipelineException = type[BaseException]
DEFAULT_FETCH_EXCEPTIONS: tuple[PipelineException, ...] = (
    OSError,
    TimeoutError,
    ValueError,
    RuntimeError,
)
DEFAULT_DATE_COLUMNS = (
    "interval",
    "commissioning_date",
    "closure_date",
    "commenced",
    "retired",
    "month",
    "date",
)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure timestamped console logging for command-line pipeline runs."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    return logging.getLogger(LOGGER_NAME)


def cache_is_fresh(path: Path, max_age_h: float = CACHE_MAX_AGE_H) -> bool:
    """Return True when a cache file exists and is younger than max_age_h."""
    if not path.exists():
        return False
    age_h = (time.time() - path.stat().st_mtime) / 3600
    return age_h < max_age_h


def coerce_datetime_columns(
    df: pd.DataFrame,
    columns: Iterable[str] = DEFAULT_DATE_COLUMNS,
    *,
    utc: bool = True,
) -> pd.DataFrame:
    """Coerce known datetime columns in-place and return the DataFrame."""
    for col in columns:
        if col in df.columns:
            parsed = pd.to_datetime(df[col], utc=utc)
            df[col] = parsed.dt.tz_localize(None) if utc else parsed
    return df


def summarize(path: Path, df: pd.DataFrame, note: str = "", logger: logging.Logger | None = None) -> None:
    """Log a short summary of a saved dataset."""
    log = logger or logging.getLogger(LOGGER_NAME)
    size_kb = path.stat().st_size / 1024 if path.exists() else 0
    date_cols = [c for c in df.columns if "interval" in c.lower() or "date" in c.lower()]
    drange = ""
    if date_cols:
        col = date_cols[0]
        drange = f" | {col}: {df[col].min()} -> {df[col].max()}"
    suffix = f" {note}" if note else ""
    log.info("  saved %s: %s rows, %.1f KB%s%s", path.name, f"{len(df):,}", size_kb, drange, suffix)


def merge_historical(
    path: Path,
    df: pd.DataFrame,
    *,
    date_columns: Iterable[str] = DEFAULT_DATE_COLUMNS,
    value_columns: Iterable[str] = ("value", "price"),
) -> pd.DataFrame:
    """Merge fetched data with an existing CSV using the legacy dedupe rules."""
    df_old = pd.read_csv(path, low_memory=False)
    coerce_datetime_columns(df_old, date_columns)
    coerce_datetime_columns(df, date_columns)

    combined = pd.concat([df_old, df], ignore_index=True)
    if "interval" in combined.columns:
        value_set = set(value_columns)
        subset_cols = [c for c in combined.columns if c not in value_set]
        combined = combined.drop_duplicates(subset=subset_cols, keep="last")
        combined = combined.sort_values("interval")
    else:
        subset_cols = [c for c in ["code", "unit_code", "facility_code"] if c in combined.columns]
        if subset_cols:
            combined = combined.drop_duplicates(subset=subset_cols, keep="last")
        else:
            combined = combined.drop_duplicates(keep="last")
    return combined.copy()


def fetch_cached(
    path: Path,
    label: str,
    fetch_fn: Callable[[], pd.DataFrame | None],
    *,
    max_age_h: float = CACHE_MAX_AGE_H,
    date_columns: Iterable[str] = DEFAULT_DATE_COLUMNS,
    exceptions: tuple[PipelineException, ...] = DEFAULT_FETCH_EXCEPTIONS,
    logger: logging.Logger | None = None,
) -> pd.DataFrame | None:
    """Read a fresh cache or fetch, merge, and save a dataset."""
    log = logger or logging.getLogger(LOGGER_NAME)
    log.info("")
    log.info("[%s] -> %s", label, path.name)
    if cache_is_fresh(path, max_age_h=max_age_h):
        df = pd.read_csv(path, low_memory=False)
        coerce_datetime_columns(df, date_columns)
        log.info("  cache hit (< %sh old), skipping API call.", max_age_h)
        summarize(path, df, logger=log)
        return df

    try:
        df = fetch_fn()
    except exceptions as exc:
        log.error("  FETCH FAILED: %s: %s", type(exc).__name__, exc)
        if path.exists():
            log.warning("  using stale cache as fallback.")
            df_fallback = pd.read_csv(path, low_memory=False)
            return coerce_datetime_columns(df_fallback, date_columns)
        return None

    if df is None or df.empty:
        log.warning("  API returned no data.")
        return df

    if path.exists():
        log.info("  merging new data with existing historical data...")
        df = merge_historical(path, df, date_columns=date_columns)

    df.to_csv(path, index=False)
    summarize(path, df, logger=log)
    return df
