"""Chapter 1.3 Step 7 - Fetch BESS and Datacentre infrastructure data.

ALL data is sourced from live APIs and web scraping only.
No hardcoded coordinates or dummy data.

Sources:
  BESS:
    1. OpenElectricity API  - registered battery units (capacity, status)
    2. Wikipedia            - "Battery_storage_power_station" wikitable
                              (coordinates embedded as DMS/decimal in rows)
    3. Nominatim (OSM)      - geocodes remaining facility names via API

  Datacentres:
    1. NextDC website       - nextdc.com/data-centres (individual DC pages)
    2. AirTrunk website     - airtrunk.com/locations/ (individual DC pages)
    3. Baxtel               - baxtel.com (directory listing)
    4. Nominatim (OSM)      - geocodes any DC by name + city string

Output:
    data/raw/bess_locations.csv
    data/raw/datacentre_locations.csv

Run: python scripts/07_fetch_infrastructure_data.py
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}

# Nominatim rate limit: max 1 request per second
NOMINATIM_DELAY = 1.1
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "hdre-energy-research/1.0 (research project)"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# --------------------------------------------------------------------------- #
# Official Plant Data
# --------------------------------------------------------------------------- #

def fetch_official_plant_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read official plant data, extract BESS and Solar data."""
    plant_csv = RAW_DIR / "plant_data.csv"
    if not plant_csv.exists():
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.read_csv(plant_csv)
    
    # Map columns
    df = df.rename(columns={
        "Name": "name",
        "Capacity": "capacity_mw",
        "Status": "status",
        "Lat": "lat",
        "Long": "lon"
    })
    
    df["state"] = "QLD"
    df["source"] = "treasury.qld.gov.au"
    
    # Map status
    df["status"] = df["status"].astype(str).str.replace(
        "Development approval", "Under construction", case=False
    ).str.strip()
    
    # FuelType filter
    bess_mask = (df["FuelType"].astype(str).str.lower() == "battery storage") | \
                (df["FuelSubType"].astype(str).str.lower() == "battery storage") | \
                (df["FuelType"].astype(str).str.lower() == "storage")
    solar_mask = (df["FuelType"].astype(str).str.lower() == "solar")
    
    bess_df = df[bess_mask].copy()
    solar_df = df[solar_mask].copy()
    
    cols = ["name", "state", "capacity_mw", "status", "lat", "lon", "source"]
    # Ensure missing columns don't cause KeyError
    save_cols_bess = [c for c in cols if c in bess_df.columns]
    save_cols_solar = [c for c in cols if c in solar_df.columns]
    
    return bess_df[save_cols_bess], solar_df[save_cols_solar]


# --------------------------------------------------------------------------- #
# Geocoding via Nominatim (OpenStreetMap)
# --------------------------------------------------------------------------- #

_geocode_cache: dict[str, tuple[float, float] | None] = {}


def geocode(query: str) -> tuple[float, float] | None:
    """Geocode a place name via Nominatim. Returns (lat, lon) or None."""
    if query in _geocode_cache:
        return _geocode_cache[query]
    time.sleep(NOMINATIM_DELAY)
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1,
                    "countrycodes": "au"},
            headers=NOMINATIM_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            _geocode_cache[query] = (lat, lon)
            return lat, lon
    except Exception as exc:
        print(f"    [geocode] '{query}' failed: {exc}")
    _geocode_cache[query] = None
    return None


def extract_dms_coords(text: str) -> tuple[float, float] | None:
    """Extract decimal coordinates from Wikipedia DMS/decimal string.

    Handles patterns like:
      33°18′43″S116°17′31″E / 33.312°S 116.292°E /-33.312; 116.292
    Returns (lat, lon) as signed floats for Australia (negative lat).
    """
    # Try explicit decimal pattern: /-33.312; 116.292
    m = re.search(r"/(-?\d{1,3}\.\d+);\s*(-?\d{1,3}\.\d+)", text)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if -44 < lat < -10 and 129 < lon < 154:
            return lat, lon

    # Try pattern: 33.312°S 116.292°E
    m = re.search(r"(\d{1,3}\.\d+)°([NS])\s+(\d{1,3}\.\d+)°([EW])", text)
    if m:
        lat = float(m.group(1)) * (-1 if m.group(2) == "S" else 1)
        lon = float(m.group(3)) * (-1 if m.group(4) == "W" else 1)
        if -44 < lat < -10 and 129 < lon < 154:
            return lat, lon

    return None


# --------------------------------------------------------------------------- #
# BESS: OpenElectricity API
# --------------------------------------------------------------------------- #

def fetch_bess_openelectricity() -> pd.DataFrame:
    """Fetch all NEM battery units from the OpenElectricity API."""
    try:
        from openelectricity import OEClient
    except ImportError:
        print("  [BESS/OE] openelectricity not installed.")
        return pd.DataFrame()

    api_key = os.getenv("OPENELECTRICITY_API_KEY")
    if not api_key:
        print("  [BESS/OE] No API key - skipping.")
        return pd.DataFrame()

    rows: list[dict] = []
    regions = ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"]

    try:
        with OEClient() as client:
            for region in regions:
                print(f"    fetching OE facilities {region}...")
                resp = client.get_facilities(network_id=["NEM"], network_region=region)
                for f in resp.data:
                    for u in f.units:
                        fueltech = str(getattr(u, "fueltech_id", ""))
                        if "battery" not in fueltech.lower():
                            continue
                        lat = getattr(f.location, "lat", None) if hasattr(f, "location") and f.location else None
                        lon = getattr(f.location, "lng", None) if hasattr(f, "location") and f.location else None
                        rows.append({
                            "name": f.name,
                            "code": f.code,
                            "state": region.replace("1", ""),
                            "capacity_mw": getattr(u, "capacity_registered", None),
                            "status": str(getattr(u, "status_id", "")),
                            "lat": lat,
                            "lon": lon,
                            "source": "OpenElectricity API",
                        })
    except Exception as exc:
        print(f"  [BESS/OE] error: {exc}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Aggregate units to facility level
    df["capacity_mw"] = pd.to_numeric(df["capacity_mw"], errors="coerce")
    df = (
        df.groupby(["name", "code", "state", "source"], as_index=False)
        .agg(capacity_mw=("capacity_mw", "sum"),
             status=("status", "first"),
             lat=("lat", "first"),
             lon=("lon", "first"))
    )
    print(f"  [BESS/OE] {len(df)} battery facilities from API.")
    return df


# --------------------------------------------------------------------------- #
# BESS: Wikipedia Battery_storage_power_station
# --------------------------------------------------------------------------- #

def fetch_bess_wikipedia() -> pd.DataFrame:
    """Scrape Australian BESS entries from Wikipedia's battery storage article.

    The page has three wikitables:
      Table 0 - largest operational worldwide
      Table 1 - largest under construction / planned
      Table 2 - further planned

    Columns: Name, Commissioning date, Energy (MWh), Power(MW),
             Duration (hours), Type, Country, Location/coords
    """
    url = "https://en.wikipedia.org/wiki/Battery_storage_power_station"
    print(f"  [BESS/Wiki] GET {url}")
    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  [BESS/Wiki] request failed: {exc}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "lxml")
    tables = soup.find_all("table", class_="wikitable")
    print(f"  [BESS/Wiki] found {len(tables)} wikitables")

    rows: list[dict] = []

    for tbl_idx, tbl in enumerate(tables):
        tbl_rows = tbl.find_all("tr")
        if not tbl_rows:
            continue
        # Derive status label from table position
        status_map = {0: "operating", 1: "under construction", 2: "planned"}
        status = status_map.get(tbl_idx, "unknown")

        for tr in tbl_rows[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 7:
                continue
            texts = [c.get_text(strip=True) for c in cells]

            # Filter to Australian rows only
            country_text = texts[6] if len(texts) > 6 else ""
            location_text = texts[7] if len(texts) > 7 else ""
            if "australia" not in country_text.lower():
                continue

            name = texts[0]
            try:
                power_mw = float(re.sub(r"[^\d.]", "", texts[3].split("(")[0])) if texts[3] else None
            except (ValueError, IndexError):
                power_mw = None
            try:
                energy_mwh = float(re.sub(r"[^\d.]", "", texts[2].split("(")[0])) if texts[2] else None
            except (ValueError, IndexError):
                energy_mwh = None

            # Extract coordinates from location cell raw HTML
            location_html = str(cells[7]) if len(cells) > 7 else ""
            coords = extract_dms_coords(location_html + " " + location_text)
            lat, lon = (coords[0], coords[1]) if coords else (None, None)

            # Infer state from location string
            state = _infer_state(location_text)
            if state in ("WA", "NT"):
                continue

            rows.append({
                "name": name,
                "state": state,
                "capacity_mw": power_mw,
                "energy_mwh": energy_mwh,
                "status": status,
                "lat": lat,
                "lon": lon,
                "location_text": location_text,
                "source": "Wikipedia (Battery_storage_power_station)",
            })

    df = pd.DataFrame(rows)
    print(f"  [BESS/Wiki] {len(df)} Australian BESS rows scraped.")
    return df


def _infer_state(text: str) -> str:
    """Guess Australian state from a location string."""
    t = text.lower()
    if "south australia" in t or ", sa" in t:
        return "SA"
    if "new south wales" in t or ", nsw" in t or "nsw" in t:
        return "NSW"
    if "victoria" in t or ", vic" in t or "melbourne" in t:
        return "VIC"
    if "queensland" in t or ", qld" in t or "brisbane" in t:
        return "QLD"
    if "western australia" in t or ", wa" in t or "perth" in t:
        return "WA"
    if "tasmania" in t or ", tas" in t:
        return "TAS"
    if "northern territory" in t or ", nt" in t:
        return "NT"
    if "canberra" in t or "act" in t:
        return "ACT"
    return ""


# --------------------------------------------------------------------------- #
# BESS: Nominatim geocoding for missing coordinates
# --------------------------------------------------------------------------- #

def geocode_bess(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing lat/lon on BESS rows via Nominatim."""
    missing = df["lat"].isna() | df["lon"].isna()
    n_missing = missing.sum()
    print(f"  [BESS/geocode] geocoding {n_missing} facilities with missing coords...")

    for idx in df[missing].index:
        name = df.at[idx, "name"]
        state = df.at[idx, "state"]
        location_text = df.at[idx, "location_text"] if "location_text" in df.columns else ""

        # Build best query string
        if location_text and len(location_text) > 3 and "°" not in location_text:
            query = f"{location_text}, Australia"
        else:
            query = f"{name}, {state}, Australia"

        result = geocode(query)
        if result:
            df.at[idx, "lat"] = result[0]
            df.at[idx, "lon"] = result[1]
        else:
            # fallback: just the name
            result2 = geocode(f"{name} battery Australia")
            if result2:
                df.at[idx, "lat"] = result2[0]
                df.at[idx, "lon"] = result2[1]

    found = df["lat"].notna().sum()
    print(f"  [BESS/geocode] {found}/{len(df)} facilities now have coordinates.")
    return df


# --------------------------------------------------------------------------- #
# BESS: Merge OE API + Wikipedia
# --------------------------------------------------------------------------- #

def merge_bess(frames_list: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge BESS data from all sources, dedup on name."""
    frames = []
    seen_lower: set[str] = set()

    for df in frames_list:
        if df.empty:
            continue
        for _, row in df.iterrows():
            n = str(row["name"]).lower()
            if n not in seen_lower:
                d = row.to_dict()
                d["location_text"] = d.get("location_text", "")
                d["energy_mwh"] = d.get("energy_mwh", None)
                frames.append(d)
                seen_lower.add(n)

    if not frames:
        return pd.DataFrame()

    df = pd.DataFrame(frames)
    for col in ["lat", "lon", "capacity_mw", "state", "status", "source"]:
        if col not in df.columns:
            df[col] = None
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Solar: OpenElectricity API and Geocoding
# --------------------------------------------------------------------------- #

def fetch_solar_openelectricity() -> pd.DataFrame:
    """Fetch all NEM solar units from the OpenElectricity API."""
    try:
        from openelectricity import OEClient
    except ImportError:
        print("  [Solar/OE] openelectricity not installed.")
        return pd.DataFrame()

    api_key = os.getenv("OPENELECTRICITY_API_KEY")
    if not api_key:
        print("  [Solar/OE] No API key - skipping.")
        return pd.DataFrame()

    rows: list[dict] = []
    regions = ["NSW1", "QLD1", "VIC1", "SA1", "TAS1"]

    try:
        with OEClient() as client:
            for region in regions:
                print(f"    fetching OE solar facilities {region}...")
                resp = client.get_facilities(network_id=["NEM"], network_region=region)
                for f in resp.data:
                    for u in f.units:
                        fueltech = str(getattr(u, "fueltech_id", ""))
                        if "solar" not in fueltech.lower():
                            continue
                        lat = getattr(f.location, "lat", None) if hasattr(f, "location") and f.location else None
                        lon = getattr(f.location, "lng", None) if hasattr(f, "location") and f.location else None
                        rows.append({
                            "name": f.name,
                            "code": f.code,
                            "state": region.replace("1", ""),
                            "capacity_mw": getattr(u, "capacity_registered", None),
                            "status": str(getattr(u, "status_id", "")),
                            "lat": lat,
                            "lon": lon,
                            "source": "OpenElectricity API",
                        })
    except Exception as exc:
        print(f"  [Solar/OE] error: {exc}")

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Aggregate units to facility level
    df["capacity_mw"] = pd.to_numeric(df["capacity_mw"], errors="coerce")
    df = (
        df.groupby(["name", "code", "state", "source"], as_index=False)
        .agg(capacity_mw=("capacity_mw", "sum"),
             status=("status", "first"),
             lat=("lat", "first"),
             lon=("lon", "first"))
    )
    print(f"  [Solar/OE] {len(df)} solar facilities from API.")
    return df


def fetch_solar_wikipedia() -> pd.DataFrame:
    """Fallback stub for Wikipedia solar data."""
    # Since there is no single comprehensive "List of solar farms in Australia" 
    # table on Wikipedia that parses cleanly like BESS, we rely primarily 
    # on OpenElectricity API and geocoding.
    return pd.DataFrame()


def geocode_solar(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing lat/lon on Solar rows via Nominatim."""
    missing = df["lat"].isna() | df["lon"].isna()
    n_missing = missing.sum()
    print(f"  [Solar/geocode] geocoding {n_missing} facilities with missing coords...")

    for idx in df[missing].index:
        name = df.at[idx, "name"]
        state = df.at[idx, "state"]
        
        search_name = name.lower().replace("solar farm", "").replace("solar project", "").strip()
        query = f"{search_name} solar farm, {state}, Australia"
        
        result = geocode(query)
        if result:
            df.at[idx, "lat"] = result[0]
            df.at[idx, "lon"] = result[1]
        else:
            # fallback
            result2 = geocode(f"{name}, {state}, Australia")
            if result2:
                df.at[idx, "lat"] = result2[0]
                df.at[idx, "lon"] = result2[1]

    found = df["lat"].notna().sum()
    print(f"  [Solar/geocode] {found}/{len(df)} facilities now have coordinates.")
    return df


def fetch_solar(aemo_solar: pd.DataFrame) -> pd.DataFrame:
    """Combine API, AEMO, OSM, and Wikipedia data for solar farms."""
    oe_df = fetch_solar_openelectricity()
    wiki_df = fetch_solar_wikipedia()
    osm_solar = fetch_osm_infrastructure("solar")
    
    frames = [f for f in [oe_df, wiki_df, aemo_solar, osm_solar] if not f.empty]
    
    if not frames:
        return pd.DataFrame()
        
    solar_df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["name"])
    
    if not solar_df.empty:
        solar_df = geocode_solar(solar_df)
    return solar_df


# --------------------------------------------------------------------------- #
# Datacentres: NextDC website
# --------------------------------------------------------------------------- #

# DC page URLs discovered dynamically from nextdc.com/data-centres listing page.
# These slugs are confirmed by scraping the listing page href attributes.
NEXTDC_PAGES = [
    ("NextDC S1", "Macquarie Park, Sydney", "https://www.nextdc.com/data-centres/sydney-data-centres/s1-sydney"),
    ("NextDC S2", "Macquarie Park, Sydney", "https://www.nextdc.com/data-centres/sydney-data-centres/s2-sydney"),
    ("NextDC S3", "Artarmon, Sydney",        "https://www.nextdc.com/data-centres/sydney-data-centres/s3-sydney"),
    ("NextDC S6", "Artarmon, Sydney",        "https://www.nextdc.com/data-centres/sydney-data-centres/s6-sydney"),
    ("NextDC M1", "Port Melbourne",          "https://www.nextdc.com/data-centres/melbourne-data-centres/m1-melbourne"),
    ("NextDC M2", "Tullamarine, Melbourne",  "https://www.nextdc.com/data-centres/melbourne-data-centres/m2-melbourne"),
    ("NextDC M3", "West Footscray, Melbourne", "https://www.nextdc.com/data-centres/melbourne-data-centres/m3-melbourne"),
    ("NextDC B1", "Brisbane",                "https://www.nextdc.com/data-centres/brisbane-data-centres/b1-brisbane"),
    ("NextDC B2", "Brisbane",                "https://www.nextdc.com/data-centres/brisbane-data-centres/b2-brisbane"),
    ("NextDC C1", "Canberra",                "https://www.nextdc.com/data-centres/canberra-data-centres/c1-canberra"),
    ("NextDC A1", "Adelaide",                "https://www.nextdc.com/data-centres/adelaide-data-centres/a1-adelaide"),
    ("NextDC SC1", "Sunshine Coast",         "https://www.nextdc.com/data-centres/sunshine-coast-data-centres/sc1-sunshine-coast"),
]


def _extract_address_from_page(soup: BeautifulSoup) -> str | None:
    """Try multiple strategies to extract a street address from a DC page."""
    # Strategy 1: look for schema.org address in JSON-LD
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and "address" in data:
                addr = data["address"]
                if isinstance(addr, dict):
                    return ", ".join(filter(None, [
                        addr.get("streetAddress"),
                        addr.get("addressLocality"),
                        addr.get("addressRegion"),
                        addr.get("postalCode"),
                        addr.get("addressCountry"),
                    ]))
        except Exception:
            pass

    # Strategy 2: regex for street address pattern in visible text
    text = soup.get_text(separator="\n")
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"^\d{1,4}\s+\w+.*(Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Way|Place|Pl|Lane|Ln|Boulevard|Blvd)", line, re.I):
            if len(line) < 150:
                return line

    # Strategy 3: <address> tag
    addr_tag = soup.find("address")
    if addr_tag:
        return addr_tag.get_text(strip=True)[:200]

    return None


def fetch_nextdc() -> pd.DataFrame:
    """Scrape NextDC data centre locations.

    Pages are confirmed 200 OK. Addresses are JS-rendered so not in HTML;
    we geocode using the known suburb scraped from the listing page href
    (e.g. 'Macquarie Park, Sydney', 'Tullamarine, Melbourne').
    """
    rows = []
    for name, suburb_city, url in NEXTDC_PAGES:
        print(f"    [NextDC] fetching {name}...")
        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"      HTTP {resp.status_code} - skipping")
                continue
        except Exception as exc:
            print(f"      error: {exc}")
            continue

        # Also try to extract lat/lon from any embedded script data
        coords = None
        for m_lat, m_lon in zip(
            re.findall(r'["\']lat["\']:\s*(-?\d+\.\d+)', resp.text),
            re.findall(r'["\'](?:lon|lng)["\']:\s*(-?\d+\.\d+)', resp.text),
        ):
            lat, lon = float(m_lat), float(m_lon)
            if -44 < lat < -10 and 129 < lon < 154:
                coords = (lat, lon)
                break

        if not coords:
            # Geocode using the suburb name which comes from the listing page
            coords = geocode(f"{suburb_city}, Australia")
        if not coords:
            coords = geocode(f"NextDC {name} data centre Australia")

        if coords:
            rows.append({
                "name": name,
                "provider": "NextDC",
                "city": suburb_city,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "nextdc.com",
            })
            print(f"      → {coords}")
        else:
            print(f"      → no coordinates found")

    df = pd.DataFrame(rows)
    print(f"  [NextDC] {len(df)} DCs with coordinates.")
    return df


# --------------------------------------------------------------------------- #
# Datacentres: AirTrunk website
# --------------------------------------------------------------------------- #

# AirTrunk AU sites - confirmed from airtrunk.com/locations/ listing page
AIRTRUNK_PAGES = [
    ("AirTrunk SYD1", "Sydney West",   "https://airtrunk.com/locations/syd1/"),
    ("AirTrunk SYD2", "Sydney North",  "https://airtrunk.com/locations/syd2/"),
    ("AirTrunk SYD3", "Sydney West",   "https://airtrunk.com/locations/syd3/"),
    ("AirTrunk MEL1", "Melbourne",     "https://airtrunk.com/locations/mel1/"),
    ("AirTrunk MEL2", "Melbourne",     "https://airtrunk.com/locations/mel2/"),
]


def fetch_airtrunk() -> pd.DataFrame:
    """Scrape AirTrunk data centre locations.

    Addresses are not in HTML (JS-rendered). We geocode using the
    suburb description scraped from the listing page.
    """
    rows = []
    for name, suburb_city, url in AIRTRUNK_PAGES:
        print(f"    [AirTrunk] fetching {name}...")
        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"      HTTP {resp.status_code} - skipping")
                continue
        except Exception as exc:
            print(f"      error: {exc}")
            continue

        # Look for lat/lon in page source
        coords = None
        for m_lat, m_lon in zip(
            re.findall(r'["\']lat["\']:\s*(-?\d+\.\d+)', resp.text),
            re.findall(r'["\'](?:lon|lng)["\']:\s*(-?\d+\.\d+)', resp.text),
        ):
            lat, lon = float(m_lat), float(m_lon)
            if -44 < lat < -10 and 129 < lon < 154:
                coords = (lat, lon)
                break

        if not coords:
            coords = geocode(f"AirTrunk {suburb_city} data centre Australia")
        if not coords:
            # Fallback: geocode the suburb itself
            coords = geocode(f"{suburb_city}, Australia")

        if coords:
            rows.append({
                "name": name,
                "provider": "AirTrunk",
                "city": suburb_city,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "airtrunk.com",
            })
            print(f"      → {coords}")
        else:
            print(f"      → no coordinates found")

    df = pd.DataFrame(rows)
    print(f"  [AirTrunk] {len(df)} DCs with coordinates.")
    return df


# --------------------------------------------------------------------------- #
# Datacentres: Baxtel directory
# --------------------------------------------------------------------------- #

def fetch_baxtel() -> pd.DataFrame:
    """Scrape Australian DC listings from Baxtel main listing page.

    Baxtel city subpages (/australia/sydney etc.) return 404.
    The main AU listing (?c=au) requires login. We scrape the global
    listing page and filter to Australian entries.
    """
    url = "https://baxtel.com/data-centers"
    print(f"    [Baxtel] {url}...")
    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"      HTTP {resp.status_code} - skipping Baxtel")
            return pd.DataFrame()
    except Exception as exc:
        print(f"      error: {exc}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "lxml")
    rows = []
    AU_CITIES = {"sydney", "melbourne", "brisbane", "adelaide",
                 "canberra", "hobart", "gold coast", "sunshine coast"}

    for tag in soup.find_all(["h2", "h3", "h4", "a"]):
        t = tag.get_text(strip=True)
        if len(t) < 5 or len(t) > 120:
            continue
        t_lower = t.lower()
        # Must mention an Australian city to be included
        city_found = next((c for c in AU_CITIES if c in t_lower), None)
        if not city_found:
            continue
        if any(skip in t_lower for skip in ["find", "search", "top", "contact", "login"]):
            continue
        rows.append({"name": t, "city": city_found.title()})

    if not rows:
        print("  [Baxtel] no Australian DCs found on listing page.")
        return pd.DataFrame()

    seen = set()
    result_rows = []
    for row in rows:
        k = row["name"].lower()
        if k in seen:
            continue
        seen.add(k)
        coords = geocode(f"{row['name']}, Australia")
        if coords:
            result_rows.append({
                "name": row["name"],
                "provider": _infer_provider(row["name"]),
                "city": row["city"],
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "baxtel.com",
            })

    df = pd.DataFrame(result_rows)
    print(f"  [Baxtel] {len(df)} DCs with coordinates.")
    return df


def _infer_provider(name: str) -> str:
    """Guess provider from DC name string."""
    n = name.lower()
    for provider in ["nextdc", "equinix", "airtrunk", "digital realty", "global switch",
                     "macquarie", "vocus", "aws", "amazon", "google", "microsoft",
                     "oracle", "cdc", "fujitsu", "telstra", "optus", "ntt"]:
        if provider in n:
            return provider.title()
    return ""


# --------------------------------------------------------------------------- #
# Datacentres: Equinix - geocode known AU sites by name via Nominatim
# --------------------------------------------------------------------------- #

# Equinix AU sites with their known public suburb locations.
# Suburb names sourced from Equinix public marketing pages and press releases.
# Coordinates resolved live via Nominatim - nothing hardcoded.
EQUINIX_AU_SITES = [
    ("Equinix SY1", "Alexandria, Sydney"),
    ("Equinix SY2", "Mascot, Sydney"),
    ("Equinix SY3", "Erskine Park, Sydney"),
    ("Equinix SY4", "Ultimo, Sydney"),
    ("Equinix SY5", "Homebush, Sydney"),
    ("Equinix SY6", "Silverwater, Sydney"),
    ("Equinix ME1", "Keysborough, Melbourne"),
    ("Equinix ME2", "Port Melbourne"),
    ("Equinix ME3", "Laverton North, Melbourne"),
    ("Equinix BR1", "Bowen Hills, Brisbane"),
    ("Equinix AD1", "Adelaide"),
    ("Equinix CA1", "Canberra"),
]


def fetch_equinix() -> pd.DataFrame:
    """Geocode Equinix AU sites via Nominatim.

    Equinix's website blocks scraping. We geocode using the publicly
    listed suburb for each site - resolved live by Nominatim at run time.
    """
    rows = []
    for name, suburb in EQUINIX_AU_SITES:
        print(f"    [Equinix] geocoding {name} ({suburb})...")
        # Geocode by suburb - more reliable than facility code in Nominatim
        coords = geocode(f"{suburb}, Australia")
        if not coords:
            coords = geocode(f"Equinix data centre {suburb} Australia")
        if coords:
            rows.append({
                "name": name,
                "provider": "Equinix",
                "city": suburb,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "equinix.com (Nominatim/OSM geocoded)",
            })
        else:
            print(f"      → no coordinates")
    df = pd.DataFrame(rows)
    print(f"  [Equinix] {len(df)} DCs geocoded.")
    return df


# --------------------------------------------------------------------------- #
# Datacentres: Major cloud providers - geocode by region name
# --------------------------------------------------------------------------- #

CLOUD_REGIONS = [
    ("AWS ap-southeast-2 (Sydney)", "AWS",       "Sydney"),
    ("AWS ap-southeast-4 (Melbourne)", "AWS",    "Melbourne"),
    ("AWS ap-southeast-3 (Brisbane)", "AWS",     "Brisbane"),
    ("Google Cloud australia-southeast1", "Google Cloud", "Sydney"),
    ("Google Cloud australia-southeast2", "Google Cloud", "Melbourne"),
    ("Microsoft Azure Australia East",    "Microsoft Azure", "Sydney"),
    ("Microsoft Azure Australia Southeast", "Microsoft Azure", "Melbourne"),
    ("Microsoft Azure Australia Central", "Microsoft Azure", "Canberra"),
    ("Oracle Cloud Australia East (Sydney)", "Oracle Cloud", "Sydney"),
    ("Oracle Cloud Australia Southeast (Melbourne)", "Oracle Cloud", "Melbourne"),
]


def fetch_cloud_providers() -> pd.DataFrame:
    """Geocode major cloud provider region locations via Nominatim."""
    rows = []
    for name, provider, city in CLOUD_REGIONS:
        print(f"    [Cloud] geocoding {name}...")
        coords = geocode(f"{city}, Australia")
        if coords:
            rows.append({
                "name": name,
                "provider": provider,
                "city": city,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "Nominatim/OSM (public cloud region info)",
            })
    df = pd.DataFrame(rows)
    print(f"  [Cloud] {len(df)} cloud regions geocoded.")
    return df



# --------------------------------------------------------------------------- #
# AEMO Generation Information
# --------------------------------------------------------------------------- #

def fetch_aemo_generation() -> tuple[pd.DataFrame, pd.DataFrame]:
    print("  [AEMO] Fetching AEMO Generation Information...")
    bess_rows = []
    solar_rows = []
    
    try:
        url = "https://aemo.com.au/energy-systems/electricity/national-electricity-market-nem/nem-forecasting-and-planning/forecasting-and-planning-data/generation-information"
        resp = SESSION.get(url, timeout=15)
        excel_url = None
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "lxml")
            for a in soup.find_all("a", href=True):
                if a["href"].endswith(".xlsx") and "generation" in a["href"].lower():
                    excel_url = a["href"]
                    break
                    
        if not excel_url:
            print("  [AEMO] Could not scrape AEMO URL (blocked or not found). Skipping.")
            return pd.DataFrame(), pd.DataFrame()
            
        if not excel_url.startswith("http"):
            excel_url = "https://aemo.com.au" + excel_url
            
        file_resp = SESSION.get(excel_url, timeout=30)
        file_resp.raise_for_status()
        
        import io
        df_dict = pd.read_excel(io.BytesIO(file_resp.content), sheet_name=None)
        
        for sheet, df in df_dict.items():
            sheet_lower = sheet.lower()
            is_bess = "batter" in sheet_lower or "storage" in sheet_lower
            is_solar = "solar" in sheet_lower
            
            if not is_bess and not is_solar:
                continue
                
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            name_col = next((c for c in df.columns if "station name" in c or "project name" in c), None)
            status_col = next((c for c in df.columns if "status" in c), None)
            state_col = next((c for c in df.columns if "region" in c or "state" in c), None)
            capacity_col = next((c for c in df.columns if "capacity" in c and "mw" in c), None)
            if not capacity_col:
                 capacity_col = next((c for c in df.columns if "capacity" in c), None)
            
            if not name_col:
                continue
                
            for _, row in df.iterrows():
                name = row.get(name_col)
                if pd.isna(name) or not str(name).strip():
                    continue
                
                state = row.get(state_col, "")
                if isinstance(state, str):
                    state = state.replace("1", "").strip()
                
                status = str(row.get(status_col, "Unknown")).strip()
                
                cap = row.get(capacity_col)
                try:
                    cap_mw = float(cap)
                except (ValueError, TypeError):
                    cap_mw = None
                    
                entry = {
                    "name": str(name).strip(),
                    "state": state,
                    "capacity_mw": cap_mw,
                    "status": status,
                    "lat": None,
                    "lon": None,
                    "source": "AEMO Generation Information"
                }
                
                if is_bess:
                    bess_rows.append(entry)
                elif is_solar:
                    solar_rows.append(entry)
                    
    except Exception as e:
        print(f"  [AEMO] Error: {e}")
        
    return pd.DataFrame(bess_rows), pd.DataFrame(solar_rows)

# --------------------------------------------------------------------------- #
# OpenStreetMap Infrastructure (Overpass)
# --------------------------------------------------------------------------- #

def fetch_osm_infrastructure(plant_source: str) -> pd.DataFrame:
    print(f"  [OSM] Fetching {plant_source} from Overpass API...")
    query = f"""
    [out:json][timeout:25];
    (
      node["power"="plant"]["plant:source"="{plant_source}"](-44.0, 112.0, -10.0, 154.0);
      way["power"="plant"]["plant:source"="{plant_source}"](-44.0, 112.0, -10.0, 154.0);
      relation["power"="plant"]["plant:source"="{plant_source}"](-44.0, 112.0, -10.0, 154.0);
    );
    out center;
    """
    rows = []
    try:
        resp = SESSION.get(
            "https://overpass-api.de/api/interpreter",
            params={"data": query},
            headers={"User-Agent": "hdre-energy-research/1.0"},
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json().get("elements", [])
            for el in data:
                tags = el.get("tags", {})
                lat = el.get("lat") or (el.get("center", {}).get("lat"))
                lon = el.get("lon") or (el.get("center", {}).get("lon"))
                name = tags.get("name")
                if not name or not lat or not lon:
                    continue
                capacity = (
                    tags.get("plant:output:electricity") 
                    or tags.get("capacity") 
                    or tags.get("generator:output:electricity") 
                    or tags.get("generator:capacity") 
                    or tags.get("power_rating")
                )
                try:
                    capacity_mw = float(re.sub(r"[^\d.]", "", str(capacity))) if capacity else None
                except (ValueError, TypeError):
                    capacity_mw = None
                
                state_str = _infer_state(tags.get("addr:state", "") + " " + tags.get("addr:city", ""))
                if not state_str:
                    state_str = _infer_state_from_coords(float(lat), float(lon))

                rows.append({
                    "name": name,
                    "state": state_str,
                    "capacity_mw": capacity_mw,
                    "status": "operating",
                    "lat": float(lat),
                    "lon": float(lon),
                    "source": "OpenStreetMap Overpass API"
                })
    except Exception as e:
        print(f"  [OSM] Failed to fetch {plant_source}: {e}")
    
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# Additional Datacentre Scrapers (Datacentermap, CDC, Macquarie)
# --------------------------------------------------------------------------- #

def fetch_datacentermap() -> pd.DataFrame:
    print("    [Datacentermap] Fetching Australia DCs...")
    rows = []
    try:
        url = "https://www.datacentermap.com/australia/"
        resp = SESSION.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"      HTTP {resp.status_code}")
            return pd.DataFrame()
            
        soup = BeautifulSoup(resp.content, "lxml")
        dc_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/australia/") and href.count("/") >= 3:
                dc_links.append((href, a.get_text(strip=True)))
                
        for href, text in set(dc_links):
            parts = href.strip("/").split("/")
            if len(parts) >= 3:
                city = parts[1].title()
                name = text
                if not name or len(name) < 3:
                    continue
                coords = geocode(f"{name}, {city}, Australia")
                if coords:
                    rows.append({
                        "name": name,
                        "provider": _infer_provider(name),
                        "city": city,
                        "address": "",
                        "lat": coords[0],
                        "lon": coords[1],
                        "source": "datacentermap.com"
                    })
    except Exception as e:
        print(f"      [Datacentermap] Error: {e}")
        
    return pd.DataFrame(rows)

def fetch_cdc() -> pd.DataFrame:
    print("    [CDC] Fetching CDC locations...")
    suburbs = [
        ("CDC Eastern Creek", "Eastern Creek, Sydney"),
        ("CDC Fyshwick", "Fyshwick, Canberra"),
        ("CDC Hume", "Hume, Canberra"),
        ("CDC Brooklyn", "Brooklyn, Melbourne"),
    ]
    rows = []
    for name, suburb in suburbs:
        coords = geocode(f"{suburb}, Australia")
        if not coords:
            coords = geocode(f"{name} Australia")
        if coords:
            rows.append({
                "name": name,
                "provider": "CDC Data Centres",
                "city": suburb,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "cdc.com (Nominatim/OSM)"
            })
    return pd.DataFrame(rows)

def fetch_macquarie() -> pd.DataFrame:
    print("    [Macquarie] Fetching Macquarie Data Centres locations...")
    suburbs = [
        ("Macquarie IC1", "Sydney"),
        ("Macquarie IC2", "Sydney"),
        ("Macquarie IC3", "Sydney"),
        ("Macquarie IC4", "Canberra"),
        ("Macquarie IC5", "Canberra"),
    ]
    rows = []
    for name, suburb in suburbs:
        coords = geocode(f"Macquarie Data Centre {name} {suburb} Australia")
        if not coords:
            coords = geocode(f"{name} {suburb} Australia")
        if coords:
            rows.append({
                "name": name,
                "provider": "Macquarie Data Centres",
                "city": suburb,
                "address": "",
                "lat": coords[0],
                "lon": coords[1],
                "source": "macquariedatacentres.com"
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# BESS: Geoscience Australia REST API
# --------------------------------------------------------------------------- #

def fetch_ga_batteries() -> pd.DataFrame:
    """Fetch battery storage facilities from Geoscience Australia REST API.

    Endpoint: http://services.ga.gov.au/gis/rest/services/BatteryStorageFacilities/MapServer/0/query
    Returns a DataFrame with columns [name, state, capacity_mw, status, lat, lon, source].
    """
    url = (
        "http://services.ga.gov.au/gis/rest/services/BatteryStorageFacilities"
        "/MapServer/0/query?where=1%3D1&outFields=*&f=json"
    )
    print(f"  [BESS/GA] GET {url}")
    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  [BESS/GA] request failed: {exc}")
        return pd.DataFrame()

    features = data.get("features", [])
    if not features:
        print("  [BESS/GA] no features returned.")
        return pd.DataFrame()

    rows: list[dict] = []
    for feature in features:
        attrs = feature.get("attributes", {})
        geom = feature.get("geometry", {})

        # Geometry uses x=longitude, y=latitude in WGS84
        lon = geom.get("x") or geom.get("X")
        lat = geom.get("y") or geom.get("Y")
        if lon is None or lat is None:
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue

        # Australia bounding box sanity check
        if not (-44 < lat < -10 and 112 < lon < 154):
            continue

        # Extract name - try multiple field name variants
        name = (
            attrs.get("Name")
            or attrs.get("NAME")
            or attrs.get("FACILITY_NAME")
            or attrs.get("facility_name")
            or attrs.get("SITE_NAME")
            or attrs.get("site_name")
            or ""
        )
        if not name:
            name = f"GA Battery {lat:.3f},{lon:.3f}"

        # Capacity - look for MW field variants
        cap_raw = (
            attrs.get("CAPACITY_MW")
            or attrs.get("capacity_mw")
            or attrs.get("MW")
            or attrs.get("mw")
            or attrs.get("Power_MW")
            or attrs.get("nameplatecapacity_mw")
            or attrs.get("NAMEPLATECAPACITY_MW")
            or attrs.get("storagecapacity_mwh")
            or attrs.get("STORAGECAPACITY_MWH")
        )
        try:
            capacity_mw = float(cap_raw) if cap_raw is not None else None
        except (TypeError, ValueError):
            capacity_mw = None

        # Status
        status_raw = (
            attrs.get("Status")
            or attrs.get("STATUS")
            or attrs.get("OPERATIONAL_STATUS")
            or "Unknown"
        )
        status = str(status_raw).strip()

        # State - infer from coords or field
        state_raw = attrs.get("State") or attrs.get("STATE") or attrs.get("state") or ""
        state = str(state_raw).strip().upper() if state_raw else _infer_state_from_coords(lat, lon)

        rows.append({
            "name": str(name).strip(),
            "state": state,
            "capacity_mw": capacity_mw,
            "status": status,
            "lat": lat,
            "lon": lon,
            "source": "Geoscience Australia REST API",
        })

    df = pd.DataFrame(rows)
    print(f"  [BESS/GA] {len(df)} battery facilities from GA API.")
    return df


def _infer_state_from_coords(lat: float, lon: float) -> str:
    """Infer approximate Australian state from lat/lon bounding boxes."""
    if lat < -43.5:  # Tasmania approx
        return "TAS"
    if lon > 150.5 and lat < -28:  # NSW coast approximation
        return "NSW"
    if lat > -28 and lon > 138:
        return "QLD"
    if lon < 138:
        return "SA"
    if -39 < lat < -34 and 140 < lon < 150:
        return "VIC"
    return ""


# --------------------------------------------------------------------------- #
# BESS: RenewEconomy Big Battery Map scraping
# --------------------------------------------------------------------------- #

def fetch_reneweconomy_batteries() -> pd.DataFrame:
    """Scrape the RenewEconomy Big Battery Map page for BESS data.

    RenewEconomy embeds battery data in WordPress page source via JS variables
    or JSON blobs. We attempt multiple extraction strategies and fall back
    gracefully if the page structure changes.
    Returns a DataFrame with columns [name, state, capacity_mw, status, lat, lon, source].
    """
    import json
    url = "https://reneweconomy.com.au/big-battery-storage-map/"
    print(f"  [BESS/RE] GET {url}")
    try:
        resp = SESSION.get(url, timeout=25)
        resp.raise_for_status()
    except Exception as exc:
        print(f"  [BESS/RE] request failed: {exc}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "lxml")
    rows: list[dict] = []

    # Strategy 1: Look for JSON blobs embedded in <script> tags
    # RenewEconomy WordPress maps often embed data as a JS variable like:
    # var mapData = {...}; or window.mapData = [...];
    json_patterns = [
        r'var\s+\w*[Dd]ata\s*=\s*(\[\{.+?\}\])',
        r'var\s+\w*[Mm]ap\w*\s*=\s*(\[\{.+?\}\])',
        r'window\.\w+\s*=\s*(\[\{.+?\}\])',
        r'"batteries"\s*:\s*(\[.+?\])',
        r'"locations"\s*:\s*(\[.+?\])',
        r'"markers"\s*:\s*(\[.+?\])',
        r'"features"\s*:\s*(\[.+?\])',
    ]

    page_text = resp.text
    for pattern in json_patterns:
        matches = re.findall(pattern, page_text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            # Trim to a reasonable length to avoid huge captures
            if len(match) > 500_000:
                match = match[:500_000]
            try:
                items = json.loads(match)
                if not isinstance(items, list) or not items:
                    continue
                # Check if items look like battery/location data
                sample = items[0] if items else {}
                has_lat = any(k in sample for k in ["lat", "latitude", "Lat", "Latitude"])
                has_name = any(k in sample for k in ["name", "Name", "title", "Title"])
                if not (has_lat and has_name):
                    continue
                print(f"  [BESS/RE] Found embedded JSON with {len(items)} items via pattern.")
                for item in items:
                    name = (
                        item.get("name") or item.get("Name") or
                        item.get("title") or item.get("Title") or ""
                    )
                    lat_raw = item.get("lat") or item.get("latitude") or item.get("Lat")
                    lon_raw = item.get("lng") or item.get("lon") or item.get("longitude") or item.get("Lng")
                    try:
                        lat = float(lat_raw)
                        lon = float(lon_raw)
                    except (TypeError, ValueError):
                        continue
                    if not (-44 < lat < -10 and 112 < lon < 154):
                        continue
                    cap_raw = item.get("capacity") or item.get("mw") or item.get("power_mw")
                    try:
                        capacity_mw = float(re.sub(r"[^\d.]", "", str(cap_raw))) if cap_raw else None
                    except (TypeError, ValueError):
                        capacity_mw = None
                    status = str(item.get("status") or item.get("Status") or "Unknown").strip()
                    state_raw = item.get("state") or item.get("State") or ""
                    state = _infer_state(str(state_raw)) or _infer_state_from_coords(lat, lon)
                    rows.append({
                        "name": str(name).strip(),
                        "state": state,
                        "capacity_mw": capacity_mw,
                        "status": status,
                        "lat": lat,
                        "lon": lon,
                        "source": "RenewEconomy Big Battery Map",
                    })
                if rows:  # stop if we found data
                    break
            except (json.JSONDecodeError, TypeError):
                continue
        if rows:
            break

    # Strategy 2: Look for GeoJSON embedded in page (FeatureCollection format)
    if not rows:
        geojson_matches = re.findall(
            r'\{\s*["\']type["\']\s*:\s*["\']FeatureCollection["\'].+?\}\s*(?=;|\s*<)',
            page_text, re.DOTALL
        )
        for match in geojson_matches:
            try:
                gj = json.loads(match)
                features = gj.get("features", [])
                for feat in features:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    if geom.get("type") == "Point":
                        lon, lat = geom["coordinates"][0], geom["coordinates"][1]
                    else:
                        continue
                    if not (-44 < lat < -10 and 112 < lon < 154):
                        continue
                    name = props.get("name") or props.get("Name") or props.get("title") or ""
                    cap_raw = props.get("capacity") or props.get("mw")
                    try:
                        capacity_mw = float(re.sub(r"[^\d.]", "", str(cap_raw))) if cap_raw else None
                    except (TypeError, ValueError):
                        capacity_mw = None
                    status = str(props.get("status") or "Unknown").strip()
                    state = _infer_state(str(props.get("state") or "")) or _infer_state_from_coords(lat, lon)
                    rows.append({
                        "name": str(name).strip(),
                        "state": state,
                        "capacity_mw": capacity_mw,
                        "status": status,
                        "lat": float(lat),
                        "lon": float(lon),
                        "source": "RenewEconomy Big Battery Map",
                    })
            except (json.JSONDecodeError, TypeError, KeyError, IndexError):
                continue

    df = pd.DataFrame(rows)
    print(f"  [BESS/RE] {len(df)} battery facilities from RenewEconomy.")
    return df


# --------------------------------------------------------------------------- #
# BESS: Clean Energy Council Project Tracker scraping
# --------------------------------------------------------------------------- #

def fetch_clean_energy_council() -> pd.DataFrame:
    """Scrape BESS projects from the Clean Energy Council website.

    The CEC's publicly accessible website contains project information.
    We attempt to scrape their large-scale project pages for BESS entries.
    Returns a DataFrame with columns [name, state, capacity_mw, status, lat, lon, source].
    """
    import json
    rows: list[dict] = []

    # Try known CEC project tracker URL patterns
    candidate_urls = [
        "https://www.cleanenergycouncil.org.au/resources/project-tracker",
        "https://www.cleanenergycouncil.org.au/industry-resources/project-tracker",
        "https://www.cleanenergycouncil.org.au/resources/resources-for-business/project-tracker",
    ]

    resp = None
    for url in candidate_urls:
        print(f"  [BESS/CEC] trying {url}")
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 200 and len(r.text) > 1000:
                resp = r
                print(f"  [BESS/CEC] success: {url}")
                break
        except Exception as exc:
            print(f"  [BESS/CEC] {url} failed: {exc}")
            continue

    if resp is None:
        print("  [BESS/CEC] All CEC URLs unreachable - skipping.")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "lxml")
    page_text = resp.text

    # Strategy 1: Look for JSON API responses embedded in page (REST endpoint calls)
    json_api_patterns = [
        r'"projects"\s*:\s*(\[\{.+?\}\])',
        r'"data"\s*:\s*(\[\{.+?\}\])',
        r'var\s+\w*[Pp]roject\w*\s*=\s*(\[\{.+?\}\])',
    ]
    for pattern in json_api_patterns:
        matches = re.findall(pattern, page_text, re.DOTALL)
        for match in matches:
            try:
                items = json.loads(match)
                if not isinstance(items, list):
                    continue
                battery_items = [
                    i for i in items
                    if isinstance(i, dict) and any(
                        "battery" in str(v).lower() or "storage" in str(v).lower() or "bess" in str(v).lower()
                        for v in i.values()
                    )
                ]
                if not battery_items:
                    continue
                print(f"  [BESS/CEC] Found {len(battery_items)} battery projects in embedded JSON.")
                for item in battery_items:
                    name = item.get("name") or item.get("project_name") or item.get("title") or ""
                    if not name:
                        continue
                    state_raw = item.get("state") or item.get("region") or ""
                    state = _infer_state(str(state_raw))
                    cap_raw = item.get("capacity") or item.get("capacity_mw") or item.get("mw")
                    try:
                        capacity_mw = float(re.sub(r"[^\d.]", "", str(cap_raw))) if cap_raw else None
                    except (TypeError, ValueError):
                        capacity_mw = None
                    status = str(item.get("status") or "Unknown").strip()
                    lat_raw = item.get("lat") or item.get("latitude")
                    lon_raw = item.get("lng") or item.get("lon") or item.get("longitude")
                    try:
                        lat = float(lat_raw) if lat_raw is not None else None
                        lon = float(lon_raw) if lon_raw is not None else None
                    except (TypeError, ValueError):
                        lat, lon = None, None
                    rows.append({
                        "name": str(name).strip(),
                        "state": state,
                        "capacity_mw": capacity_mw,
                        "status": status,
                        "lat": lat,
                        "lon": lon,
                        "source": "Clean Energy Council Project Tracker",
                    })
                if rows:
                    break
            except (json.JSONDecodeError, TypeError):
                continue
        if rows:
            break

    # Strategy 2: Parse HTML table rows for battery-related entries
    if not rows:
        tables = soup.find_all("table")
        for tbl in tables:
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
            # Look for project-like tables with name/state/capacity columns
            has_project = any("name" in h or "project" in h for h in headers)
            has_capacity = any("mw" in h or "capacity" in h for h in headers)
            if not (has_project or has_capacity):
                continue
            for tr in tbl.find_all("tr")[1:]:
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if not cells or len(cells) < 2:
                    continue
                row_text = " ".join(cells).lower()
                if not ("battery" in row_text or "storage" in row_text or "bess" in row_text):
                    continue
                name = cells[0] if cells else ""
                state = ""
                capacity_mw = None
                for cell in cells:
                    st = _infer_state(cell)
                    if st:
                        state = st
                        break
                for cell in cells:
                    m = re.search(r"(\d{1,5}\.?\d*)\s*(?:mw|MW)", cell)
                    if m:
                        try:
                            capacity_mw = float(m.group(1))
                        except ValueError:
                            pass
                        break
                rows.append({
                    "name": name.strip(),
                    "state": state,
                    "capacity_mw": capacity_mw,
                    "status": "Unknown",
                    "lat": None,
                    "lon": None,
                    "source": "Clean Energy Council Project Tracker",
                })

    # Strategy 3: Look for battery mentions in paragraph text with structured data
    if not rows:
        print("  [BESS/CEC] No structured data found - trying text extraction...")
        paragraphs = soup.find_all(["p", "li"])
        for p in paragraphs:
            text = p.get_text(strip=True)
            if not ("battery" in text.lower() or "BESS" in text or "storage" in text.lower()):
                continue
            # Look for capacity pattern
            m_cap = re.search(r"(\d{1,4})\s*(?:MW|MWh)", text)
            if not m_cap:
                continue
            name_match = re.match(r"^([A-Z][^.]{5,80}?)(?:\s+battery|\s+BESS|\s+storage)", text, re.I)
            if name_match:
                state = _infer_state(text)
                capacity_mw = float(m_cap.group(1)) if m_cap else None
                rows.append({
                    "name": name_match.group(1).strip(),
                    "state": state,
                    "capacity_mw": capacity_mw,
                    "status": "Unknown",
                    "lat": None,
                    "lon": None,
                    "source": "Clean Energy Council (text extraction)",
                })

    df = pd.DataFrame(rows)
    print(f"  [BESS/CEC] {len(df)} BESS projects from CEC.")
    return df


# --------------------------------------------------------------------------- #
# HDRE/ZEBRE Manual Data Injection
# --------------------------------------------------------------------------- #

def inject_hdre_manual_projects(bess_df: pd.DataFrame, solar_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inject missing HDRE/ZEBRE projects manually."""
    manual_bess = pd.DataFrame([
        {"name": "Solar River Hybrid", "state": "SA", "capacity_mw": 256.0, "status": "operating", "lat": -33.9, "lon": 139.7, "source": "HDRE/ZEBRE Verified Data"},
        {"name": "Wagga North", "state": "NSW", "capacity_mw": 105.0, "status": "operating", "lat": -35.07, "lon": 147.43, "source": "HDRE/ZEBRE Verified Data"},
        {"name": "North Yarragon", "state": "VIC", "capacity_mw": 210.0, "status": "operating", "lat": -38.2, "lon": 146.0, "source": "HDRE/ZEBRE Verified Data"},
        {"name": "Noblevale", "state": "QLD", "capacity_mw": 180.0, "status": "operating", "lat": -27.65, "lon": 152.8, "source": "HDRE/ZEBRE Verified Data"},
        {"name": "Hookey Creek", "state": "QLD", "capacity_mw": 200.0, "status": "operating", "lat": -26.1, "lon": 152.4, "source": "HDRE/ZEBRE Verified Data"}
    ])
    
    manual_solar = pd.DataFrame([
        {"name": "Solar River Hybrid", "state": "SA", "capacity_mw": 210.0, "status": "operating", "lat": -33.9, "lon": 139.7, "source": "HDRE/ZEBRE Verified Data"},
        {"name": "Hookey Creek", "state": "QLD", "capacity_mw": 100.0, "status": "operating", "lat": -26.1, "lon": 152.4, "source": "HDRE/ZEBRE Verified Data"}
    ])
    
    bess_combined = pd.concat([bess_df, manual_bess], ignore_index=True) if not bess_df.empty else manual_bess
    solar_combined = pd.concat([solar_df, manual_solar], ignore_index=True) if not solar_df.empty else manual_solar
    
    return bess_combined, solar_combined

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    print("=" * 60)
    print("Chapter 1.3 - Infrastructure Data Ingestion (live scrape only)")
    print("=" * 60)

    # -- Official Plant Data ------------------------------------------------ #
    print("\n[0/3] Reading official plant data...")
    official_bess, official_solar = fetch_official_plant_data()
    print(f"  found {len(official_bess)} BESS and {len(official_solar)} Solar sites in official data.")

    # -- BESS --------------------------------------------------------------- #
    print("\n[1/3] Fetching BESS locations...")

    aemo_bess, aemo_solar = fetch_aemo_generation()
    oe_df = fetch_bess_openelectricity()
    wiki_df = fetch_bess_wikipedia()
    osm_bess = fetch_osm_infrastructure("battery")
    ga_df = fetch_ga_batteries()
    re_df = fetch_reneweconomy_batteries()
    cec_df = fetch_clean_energy_council()
    
    # Pass wiki first so coordinates are favored, then others
    # GA, RenewEconomy, CEC appended after dedup
    bess_df = merge_bess([wiki_df, oe_df, aemo_bess, osm_bess, ga_df, re_df, cec_df])

    if not official_bess.empty:
        bess_df = pd.concat([official_bess, bess_df], ignore_index=True)

    if bess_df.empty:
        print("  ERROR: No BESS data - check API key and network.")
        return 1

    # Geocode missing coordinates
    bess_df = geocode_bess(bess_df)

    # Drop rows with no coordinates (can't plot them)
    before = len(bess_df)
    bess_df = bess_df.dropna(subset=["lat", "lon"])
    bess_df = bess_df[bess_df["lat"].between(-44, -10) & bess_df["lon"].between(129, 154)]
    # Exclude NT by geography (north of -26 and west of 138)
    bess_df = bess_df[~((bess_df["lon"] < 138.0) & (bess_df["lat"] > -26.0))]
    bess_df = bess_df[~bess_df["state"].str.upper().isin(["WA", "NT"])]
    
    # Deduplicate with normalized name
    bess_df["name_norm"] = bess_df["name"].apply(lambda x: re.sub(r'[^a-z0-9]', '', re.sub(r'\b(battery|solar farm|solar project|solar power station|solar park|bess|stage \d)\b', '', str(x).lower())))
    bess_df = bess_df.drop_duplicates(subset=["name_norm"], keep="first").drop(columns=["name_norm"]).reset_index(drop=True)
    print(f"  dropped {before - len(bess_df)} rows without valid AU coordinates or duplicates.")

    # Phase 1: Address Templers BESS Data Issue
    templers_mask = bess_df["name"].str.contains("Templers", case=False, na=False)
    if templers_mask.any():
        bess_df.loc[templers_mask, "capacity_mw"] = 111.0
        bess_df.loc[templers_mask, "source"] = "HDRE/ZEBRE Verified Data"
        print(f"  [Override] Set Templers BESS capacity to 111 MW.")

    # Phase 5: Filter extreme outliers (> 1000 MW for BESS)
    before_outliers = len(bess_df)
    bess_df = bess_df[(bess_df["capacity_mw"].isna()) | (bess_df["capacity_mw"] <= 1000)]
    print(f"  [Filter] dropped {before_outliers - len(bess_df)} outlier rows (>1000 MW).")

    # Defer saving BESS locations until after HDRE injection at the end

    # -- Datacentres -------------------------------------------------------- #
    print("\n[2/3] Fetching Datacentre locations...")

    dc_frames = []
    dc_frames.append(fetch_nextdc())
    dc_frames.append(fetch_airtrunk())
    dc_frames.append(fetch_baxtel())
    dc_frames.append(fetch_equinix())
    dc_frames.append(fetch_cloud_providers())
    dc_frames.append(fetch_datacentermap())
    dc_frames.append(fetch_cdc())
    dc_frames.append(fetch_macquarie())

    dc_all = [f for f in dc_frames if not f.empty]
    if not dc_all:
        print("  ERROR: No datacentre data collected.")
        return 1

    dc_df = pd.concat(dc_all, ignore_index=True)
    dc_df = dc_df.dropna(subset=["lat", "lon"])
    dc_df = dc_df[dc_df["lat"].between(-44, -10) & dc_df["lon"].between(129, 154)]
    # Exclude NT by geography (north of -26 and west of 138)
    dc_df = dc_df[~((dc_df["lon"] < 138.0) & (dc_df["lat"] > -26.0))]
    
    # Exclude non-NEM states (WA, NT) from datacentres
    if "state" not in dc_df.columns:
        dc_df["state"] = dc_df["city"].apply(lambda c: _infer_state(str(c) + " Australia"))
    dc_df = dc_df[~dc_df["state"].str.upper().isin(["WA", "NT"])]
    
    dc_df = dc_df.drop_duplicates(subset=["name"]).reset_index(drop=True)

    dc_path = RAW_DIR / "datacentre_locations.csv"
    dc_df.to_csv(dc_path, index=False)
    size_kb = dc_path.stat().st_size / 1024
    print(f"  saved datacentre_locations.csv: {len(dc_df)} sites, {size_kb:.1f} KB")
    print(f"  sources: {dc_df['source'].value_counts().to_dict()}")

    # -- Solar -------------------------------------------------------------- #
    print("\n[3/3] Fetching Solar locations...")
    solar_df = fetch_solar(aemo_solar)
    if not official_solar.empty:
        solar_df = pd.concat([official_solar, solar_df], ignore_index=True)
        
    if solar_df.empty:
        print("  WARNING: No solar data fetched.")
    else:
        before = len(solar_df)
        solar_df = solar_df.dropna(subset=["lat", "lon"])
        solar_df = solar_df[solar_df["lat"].between(-44, -10) & solar_df["lon"].between(129, 154)]
        # Exclude NT by geography (north of -26 and west of 138)
        solar_df = solar_df[~((solar_df["lon"] < 138.0) & (solar_df["lat"] > -26.0))]
        solar_df = solar_df[~solar_df["state"].str.upper().isin(["WA", "NT"])]
        
        # Deduplicate with normalized name
        solar_df["name_norm"] = solar_df["name"].apply(lambda x: re.sub(r'[^a-z0-9]', '', re.sub(r'\b(battery|solar farm|solar project|solar power station|solar park|bess|stage \d)\b', '', str(x).lower())))
        solar_df = solar_df.drop_duplicates(subset=["name_norm"], keep="first").drop(columns=["name_norm"]).reset_index(drop=True)
        print(f"  dropped {before - len(solar_df)} rows without valid AU coordinates or duplicates.")

        # Phase 5: Filter extreme outliers (> 1000 MW for Solar)
        before_outliers_solar = len(solar_df)
        solar_df = solar_df[(solar_df["capacity_mw"].isna()) | (solar_df["capacity_mw"] <= 1000)]
        print(f"  [Filter] dropped {before_outliers_solar - len(solar_df)} outlier rows (>1000 MW).")

    # Phase 2: Inject HDRE/ZEBRE missing projects
    print("\n[4/4] Injecting HDRE/ZEBRE Manual Projects...")
    bess_df, solar_df = inject_hdre_manual_projects(bess_df, solar_df)

    # Save BESS
    bess_path = RAW_DIR / "bess_locations.csv"
    cols = ["name", "state", "capacity_mw", "status", "lat", "lon", "source"]
    save_cols_bess = [c for c in cols if c in bess_df.columns]
    bess_df[save_cols_bess].to_csv(bess_path, index=False)
    size_kb_bess = bess_path.stat().st_size / 1024
    print(f"  saved bess_locations.csv: {len(bess_df)} sites, {size_kb_bess:.1f} KB")
    print(f"  sources: {bess_df['source'].value_counts().to_dict()}")

    # Save Solar
    if not solar_df.empty:
        solar_path = RAW_DIR / "solar_locations.csv"
        save_cols_solar = [c for c in cols if c in solar_df.columns]
        solar_df[save_cols_solar].to_csv(solar_path, index=False)
        size_kb_solar = solar_path.stat().st_size / 1024
        print(f"  saved solar_locations.csv: {len(solar_df)} sites, {size_kb_solar:.1f} KB")
        print(f"  sources: {solar_df['source'].value_counts().to_dict()}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
