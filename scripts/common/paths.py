"""Shared filesystem paths for pipeline scripts."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_CH3_DIR = DATA_DIR / "processed_ch3"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIG_DIR = OUTPUT_DIR / "figures"
PNG_DIR = FIG_DIR / "png"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
LOG_DIR = PROJECT_ROOT / "logs"
NEMOSIS_CACHE_DIR = PROJECT_ROOT / "nemosis_cache"


def ensure_pipeline_dirs() -> None:
    """Create standard output directories used by the data pipeline."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
