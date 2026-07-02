"""Dashboard data-loading helpers."""

from __future__ import annotations

import streamlit as st

from scripts.common.infrastructure import load_infrastructure_frames
from scripts.common.paths import RAW_DIR


@st.cache_data
def load_infrastructure_data():
    """Load infrastructure CSVs after pipeline-owned cleaning."""
    return load_infrastructure_frames(RAW_DIR)
