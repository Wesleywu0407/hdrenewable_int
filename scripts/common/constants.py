"""Shared constants for NEM data ingestion and chart generation."""

from __future__ import annotations

from datetime import timedelta, timezone

CACHE_MAX_AGE_H = 24
NEM_TZ = timezone(timedelta(hours=10))
WEM_TZ = timezone(timedelta(hours=8))
NEM_REGIONS = ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"]

# Fueltech ID -> wide-format column name mappings.
# The double space in " -  MW" is intentional and matches the team files.
FUELTECH_POWER_COLS: dict[str, str] = {
    "battery_charging": "Battery (Charging) -  MW",
    "pumps": "Pumps -  MW",
    "coal_brown": "Coal (Brown) -  MW",
    "coal_black": "Coal (Black) -  MW",
    "bioenergy_biomass": "Bioenergy (Biomass) -  MW",
    "bioenergy_biogas": "Bioenergy (Biogas) -  MW",
    "distillate": "Distillate -  MW",
    "gas_steam": "Gas (Steam) -  MW",
    "gas_ccgt": "Gas (CCGT) -  MW",
    "gas_ocgt": "Gas (OCGT) -  MW",
    "gas_recip": "Gas (Reciprocating) -  MW",
    "gas_wcmg": "Gas (Waste Coal Mine) -  MW",
    "battery_discharging": "Battery (Discharging) -  MW",
    "hydro": "Hydro -  MW",
    "wind": "Wind -  MW",
    "solar_utility": "Solar (Utility) -  MW",
    "solar_rooftop": "Solar (Rooftop) -  MW",
}

FUELTECH_EMISSIONS_COLS: dict[str, str] = {
    "coal_brown": "Coal (Brown) Emissions Vol - tCO\u2082e",
    "coal_black": "Coal (Black) Emissions Vol - tCO\u2082e",
    "bioenergy_biomass": "Bioenergy (Biomass) Emissions Vol - tCO\u2082e",
    "bioenergy_biogas": "Bioenergy (Biogas) Emissions Vol - tCO\u2082e",
    "distillate": "Distillate Emissions Vol - tCO\u2082e",
    "gas_steam": "Gas (Steam) Emissions Vol - tCO\u2082e",
    "gas_ccgt": "Gas (CCGT) Emissions Vol - tCO\u2082e",
    "gas_ocgt": "Gas (OCGT) Emissions Vol - tCO\u2082e",
    "gas_recip": "Gas (Reciprocating) Emissions Vol - tCO\u2082e",
    "gas_wcmg": "Gas (Waste Coal Mine) Emissions Vol - tCO\u2082e",
}

FUEL_COLORS = {
    "coal": "#1a1a1a",
    "gas": "#e8722c",
    "solar": "#f4d03f",
    "wind": "#5dade2",
    "hydro": "#1f618d",
    "battery": "#27ae60",
    "bioenergy": "#7d6608",
    "distillate": "#a04000",
    "pumps": "#76448a",
    "other": "#909497",
}

REGION_LABELS = {
    "NSW1": "NSW",
    "QLD1": "QLD",
    "VIC1": "VIC",
    "SA1": "SA",
    "TAS1": "TAS",
}
REGION_COLORS = {
    "QLD1": "#8e44ad",
    "NSW1": "#3498db",
    "VIC1": "#2c3e50",
    "SA1": "#e74c3c",
    "TAS1": "#27ae60",
}
REGION_ORDER = ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]

GEN_GROUPS = ["coal", "gas", "hydro", "wind", "solar", "bioenergy", "distillate", "battery"]
STACK_ORDER = ["coal", "gas", "distillate", "hydro", "wind", "solar", "bioenergy", "battery"]
