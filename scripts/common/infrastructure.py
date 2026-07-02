"""Infrastructure data cleaning shared by the pipeline and dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CITY_STATE_RULES = (
    ("Sydney", "NSW"),
    ("Melbourne", "VIC"),
    ("Brisbane", "QLD"),
    ("Adelaide", "SA"),
    ("Perth", "WA"),
)


def normalize_facility_states(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a facility DataFrame's state column when present."""
    if df.empty or "state" not in df.columns:
        return df
    cleaned = df.copy()
    cleaned["state"] = cleaned["state"].astype(str).str.strip().str.upper()
    cleaned.loc[cleaned["state"].isin({"", "NAN", "NONE"}), "state"] = None
    return cleaned


def clean_datacentre_states(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize datacentre state values and infer missing values from city."""
    if df.empty:
        return df
    cleaned = normalize_facility_states(df)
    if "state" not in cleaned.columns:
        cleaned["state"] = None
    if "city" not in cleaned.columns:
        return cleaned
    for city_fragment, state in CITY_STATE_RULES:
        mask = cleaned["state"].isna() & cleaned["city"].astype(str).str.contains(
            city_fragment,
            case=False,
            na=False,
        )
        cleaned.loc[mask, "state"] = state
    return cleaned


def clean_infrastructure_frames(
    bess_df: pd.DataFrame,
    solar_df: pd.DataFrame,
    dc_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Clean BESS, solar, and datacentre frames consistently."""
    return (
        normalize_facility_states(bess_df),
        normalize_facility_states(solar_df),
        clean_datacentre_states(dc_df),
    )


def load_infrastructure_frames(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cleaned infrastructure CSVs from a raw data directory."""
    bess_df = pd.read_csv(raw_dir / "bess_locations.csv")
    solar_df = pd.read_csv(raw_dir / "solar_locations.csv")
    dc_df = pd.read_csv(raw_dir / "datacentre_locations.csv")
    return clean_infrastructure_frames(bess_df, solar_df, dc_df)
