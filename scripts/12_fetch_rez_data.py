"""Chapter 1.3 Step 12 - Fetch Renewable Energy Zone (REZ) polygon data.

Downloads REZ polygon boundaries from official government sources and saves
them as GeoJSON files in data/raw/ for use in the infrastructure map.

Sources:
  VIC:  VicGrid ArcGIS REST FeatureServer (free open API)
  TAS:  State Growth Tasmania ArcGIS REST MapServer (free open API)
  NSW:  EnergyCo - ArcGIS REST FeatureServer (free open API, fallback to shapefile)
  QLD:  Powerlink/AEMO - ArcGIS REST API (fallback to shapefile download)

Outputs:
  data/raw/rez_vic.geojson
  data/raw/rez_tas.geojson
  data/raw/rez_nsw.geojson
  data/raw/rez_qld.geojson

Run: python scripts/12_fetch_rez_data.py
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Optional

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# REZ zone colour palette - one per state (for rendering in Plotly)
REZ_COLORS = {
    "VIC": "#1e88e5",   # blue
    "TAS": "#43a047",   # green
    "NSW": "#fb8c00",   # orange
    "QLD": "#8e24aa",   # purple
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _save_geojson(geojson: dict, state: str, filename: str) -> Path:
    """Save a GeoJSON dict to data/raw/<filename>, excluding offshore REZ features."""
    out_path = RAW_DIR / filename

    # Filter out offshore / marine zones - we only want onshore REZs.
    # NOTE: "coast" alone is too broad (e.g. NSW "Hunter-Central Coast" is onshore).
    # Use specific multi-word patterns or explicit field values instead.
    OFFSHORE_KEYWORDS = (
        "offshore",
        "marine",
        "seabed",
        "shoreline",       # VIC: 'Gippsland Shoreline' (also caught by REZType=1)
        "tasmanian coast", # TAS: 'T4 North West Tasmanian Coast', 'T5 North East Tasmanian Coast'
    )
    onshore_features = []
    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        name = str(
            props.get("rez_name") or props.get("REZName") or
            props.get("Name") or props.get("REZ") or ""
        ).lower()
        # Also check VIC REZType field: 1 = offshore/shoreline, 0 = onshore
        rez_type = props.get("REZType")
        if rez_type == 1:
            print(f"  [REZ] Skipping offshore feature (REZType=1): {name}")
            continue
        if any(kw in name for kw in OFFSHORE_KEYWORDS):
            print(f"  [REZ] Skipping offshore feature: {name}")
            continue
        props.setdefault("state", state)
        props.setdefault("rez_color", REZ_COLORS.get(state, "#888888"))
        onshore_features.append(feature)

    geojson_out = {"type": "FeatureCollection", "features": onshore_features}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geojson_out, f, ensure_ascii=False)
    size_kb = out_path.stat().st_size / 1024
    n_features = len(onshore_features)
    print(f"  saved {filename}: {n_features} onshore features, {size_kb:.1f} KB")
    return out_path


def _fetch_arcgis_geojson(url: str, state: str, label: str) -> Optional[dict]:
    """Fetch a GeoJSON FeatureCollection from an ArcGIS REST endpoint.

    Handles pagination via the ArcGIS resultOffset/resultRecordCount mechanism.
    Returns None on failure.
    """
    all_features: list[dict] = []
    offset = 0
    record_count = 1000
    max_attempts = 10

    for attempt in range(max_attempts):
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": record_count,
        }
        print(f"  [{label}] GET {url} (offset={offset})")
        try:
            resp = SESSION.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [{label}] request failed: {exc}")
            return None

        features = data.get("features", [])
        all_features.extend(features)

        # Check if more records exist
        exceeded = data.get("exceededTransferLimit", False)
        if not exceeded or not features:
            break
        offset += len(features)
        time.sleep(0.3)

    if not all_features:
        print(f"  [{label}] no features returned from {url}")
        return None

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
    }
    print(f"  [{label}] {len(all_features)} features fetched from API.")
    return geojson


def _shp_zip_to_geojson(zip_bytes: bytes, state: str, label: str) -> Optional[dict]:
    """Convert a zipped shapefile to a GeoJSON dict using geopandas."""
    try:
        import geopandas as gpd
    except ImportError:
        print(f"  [{label}] geopandas not installed - cannot convert shapefile.")
        return None

    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        # Find the .shp file inside the zip
        shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")]
        if not shp_names:
            print(f"  [{label}] No .shp file found in ZIP.")
            return None

        # Extract to a temp dir within the project
        tmp_dir = RAW_DIR / f"_rez_tmp_{state.lower()}"
        tmp_dir.mkdir(exist_ok=True)
        zf.extractall(tmp_dir)

        shp_path = tmp_dir / shp_names[0]
        gdf = gpd.read_file(shp_path)

        # Reproject to WGS84 if needed
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
        elif gdf.crs is None:
            print(f"  [{label}] CRS unknown - assuming WGS84.")

        geojson_str = gdf.to_json()
        geojson = json.loads(geojson_str)
        print(f"  [{label}] Converted shapefile: {len(gdf)} features.")

        # Cleanup temp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

        return geojson

    except Exception as exc:
        print(f"  [{label}] Shapefile conversion failed: {exc}")
        return None


# --------------------------------------------------------------------------- #
# VIC REZ - VicGrid ArcGIS REST API (free, reliable)
# --------------------------------------------------------------------------- #

def fetch_vic_rez() -> Optional[dict]:
    """Fetch VIC Renewable Energy Zone polygons from VicGrid ArcGIS API."""
    url = (
        "https://services-ap1.arcgis.com/idfthKuhr6cmA2QX/arcgis/rest/services"
        "/VicGrid_Renewable_Energy_Zones/FeatureServer/0/query"
    )
    geojson = _fetch_arcgis_geojson(url, "VIC", "VIC/REZ")
    if geojson:
        for feat in geojson.get("features", []):
            props = feat.setdefault("properties", {})
            name = (
                props.get("REZ_Name") or props.get("REZ_ID") or
                props.get("Name") or props.get("name") or
                props.get("LABEL") or "VIC REZ"
            )
            props["rez_name"] = str(name)
            props["state"] = "VIC"
    return geojson


# --------------------------------------------------------------------------- #
# TAS REZ - State Growth Tasmania ArcGIS REST API (free, reliable)
# Layer 10: AEMO ISP Candidate REZ
# --------------------------------------------------------------------------- #

def fetch_tas_rez() -> Optional[dict]:
    """Fetch TAS Renewable Energy Zone polygons from State Growth Tasmania."""
    base_url = "https://data.stategrowth.tas.gov.au/ags/rest/services/PROJECTS/Energy_Res2/MapServer"
    geojson = None

    for layer_id in [10]:
        url = f"{base_url}/{layer_id}/query"
        geojson = _fetch_arcgis_geojson(url, "TAS", f"TAS/REZ/L{layer_id}")
        if geojson and geojson.get("features"):
            break

    if geojson:
        for feat in geojson.get("features", []):
            props = feat.setdefault("properties", {})
            name = (
                props.get("REZ_NAME") or props.get("REZ_ID") or
                props.get("Name") or props.get("name") or
                props.get("LABEL") or "TAS REZ"
            )
            props["rez_name"] = str(name)
            props["state"] = "TAS"
    return geojson


# --------------------------------------------------------------------------- #
# NSW REZ - EnergyCo (ArcGIS REST, fallback to shapefile)
# --------------------------------------------------------------------------- #

def fetch_nsw_rez() -> Optional[dict]:
    """Fetch NSW Renewable Energy Zone polygons from NSW Government ArcGIS / EnergyCo."""
    geojson = None

    # Option 1: NSW Government ArcGIS Online (confirmed working - INF_RenewableEnergyZones_3857)
    # Hosted by NSW Government on services6.arcgis.com/LHYr6B7cFUs40aCx
    energyco_endpoints = [
        "https://services6.arcgis.com/LHYr6B7cFUs40aCx/arcgis/rest/services/INF_RenewableEnergyZones_3857/FeatureServer/0/query",
        "https://services8.arcgis.com/7fBaXGVXh5DfIkqr/arcgis/rest/services/NSW_REZ_Boundaries/FeatureServer/0/query",
        "https://maps.energyco.nsw.gov.au/arcgis/rest/services/REZ/MapServer/0/query",
    ]
    for url in energyco_endpoints:
        print(f"  [NSW/REZ] trying ArcGIS: {url}")
        try:
            geojson = _fetch_arcgis_geojson(url, "NSW", "NSW/REZ")
            if geojson and geojson.get("features"):
                break
        except Exception as exc:
            print(f"  [NSW/REZ] {url} failed: {exc}")

    # Option 2: data.nsw.gov.au CKAN API
    if not geojson or not geojson.get("features"):
        print("  [NSW/REZ] trying data.nsw.gov.au CKAN API...")
        try:
            ckan_url = (
                "https://data.nsw.gov.au/api/3/action/package_search"
                "?q=renewable+energy+zone&rows=5"
            )
            cr = SESSION.get(ckan_url, timeout=15)
            if cr.status_code == 200:
                results = cr.json().get("result", {}).get("results", [])
                for pkg in results:
                    for res in pkg.get("resources", []):
                        rurl = res.get("url", "")
                        if rurl.endswith(".zip") and len(rurl) > 10:
                            print(f"  [NSW/REZ] downloading shapefile: {rurl}")
                            shp_resp = SESSION.get(rurl, timeout=60)
                            if shp_resp.status_code == 200:
                                geojson = _shp_zip_to_geojson(shp_resp.content, "NSW", "NSW/REZ")
                                if geojson and geojson.get("features"):
                                    break
                    if geojson and geojson.get("features"):
                        break
        except Exception as exc:
            print(f"  [NSW/REZ] CKAN search failed: {exc}")

    # Option 3: Known direct shapefile URLs
    if not geojson or not geojson.get("features"):
        shp_urls = [
            "https://www.energyco.nsw.gov.au/sites/default/files/REZ_boundaries_shapefiles.zip",
            "https://www.planning.nsw.gov.au/-/media/Files/DPE/Reports/renewable-energy-zones-boundary.zip",
        ]
        for url in shp_urls:
            print(f"  [NSW/REZ] trying direct shapefile: {url}")
            try:
                r = SESSION.get(url, timeout=60)
                if r.status_code == 200 and len(r.content) > 1000:
                    geojson = _shp_zip_to_geojson(r.content, "NSW", "NSW/REZ")
                    if geojson and geojson.get("features"):
                        break
            except Exception as exc:
                print(f"  [NSW/REZ] {url} failed: {exc}")

    if geojson and geojson.get("features"):
        for feat in geojson.get("features", []):
            props = feat.setdefault("properties", {})
            name = (
                props.get("REZ") or props.get("REZ_NAME") or props.get("REZ_ID") or
                props.get("Name") or props.get("name") or
                props.get("ZONE_NAME") or props.get("LABEL") or "NSW REZ"
            )
            props["rez_name"] = str(name)
            props["state"] = "NSW"

    return geojson


# --------------------------------------------------------------------------- #
# QLD REZ - Powerlink / AEMO ISP (ArcGIS REST, fallback to shapefile)
# --------------------------------------------------------------------------- #

def fetch_qld_rez() -> Optional[dict]:
    """Fetch QLD Renewable Energy Zone polygons from Powerlink / AEMO ISP."""
    geojson = None

    # Option 1: QLD Government ArcGIS REST endpoints
    qld_endpoints = [
        "https://services5.arcgis.com/PRFKXBG1bX4oYb82/arcgis/rest/services/QLD_REZ_Areas/FeatureServer/0/query",
        "https://gisservices.information.qld.gov.au/arcgis/rest/services/Economy/QG_Renewable_Energy_Zones/MapServer/0/query",
        "https://spatial.information.qld.gov.au/arcgis/rest/services/Utilities/QG_Renewable_Energy/FeatureServer/0/query",
    ]
    for url in qld_endpoints:
        print(f"  [QLD/REZ] trying ArcGIS: {url}")
        try:
            geojson = _fetch_arcgis_geojson(url, "QLD", "QLD/REZ")
            if geojson and geojson.get("features"):
                break
        except Exception as exc:
            print(f"  [QLD/REZ] {url} failed: {exc}")

    # Option 2: data.qld.gov.au CKAN API
    if not geojson or not geojson.get("features"):
        print("  [QLD/REZ] trying data.qld.gov.au CKAN API...")
        try:
            ckan_url = (
                "https://www.data.qld.gov.au/api/3/action/package_search"
                "?q=renewable+energy+zone&rows=5"
            )
            cr = SESSION.get(ckan_url, timeout=15)
            if cr.status_code == 200:
                results = cr.json().get("result", {}).get("results", [])
                for pkg in results:
                    for res in pkg.get("resources", []):
                        rurl = res.get("url", "")
                        fmt = res.get("format", "").lower()
                        if (rurl.endswith(".zip") or fmt == "shp") and len(rurl) > 10:
                            print(f"  [QLD/REZ] downloading shapefile: {rurl}")
                            shp_resp = SESSION.get(rurl, timeout=60)
                            if shp_resp.status_code == 200:
                                geojson = _shp_zip_to_geojson(shp_resp.content, "QLD", "QLD/REZ")
                                if geojson and geojson.get("features"):
                                    break
                    if geojson and geojson.get("features"):
                        break
        except Exception as exc:
            print(f"  [QLD/REZ] CKAN search failed: {exc}")

    # Option 3: Known direct shapefile URLs
    if not geojson or not geojson.get("features"):
        shp_urls = [
            "https://www.powerlink.com.au/sites/default/files/REZ_boundaries.zip",
            "https://www.energyqueensland.com.au/sites/default/files/qld-rez-shapefiles.zip",
        ]
        for url in shp_urls:
            print(f"  [QLD/REZ] trying direct shapefile: {url}")
            try:
                r = SESSION.get(url, timeout=60)
                if r.status_code == 200 and len(r.content) > 1000:
                    geojson = _shp_zip_to_geojson(r.content, "QLD", "QLD/REZ")
                    if geojson and geojson.get("features"):
                        break
            except Exception as exc:
                print(f"  [QLD/REZ] {url} failed: {exc}")

    if geojson and geojson.get("features"):
        for feat in geojson.get("features", []):
            props = feat.setdefault("properties", {})
            name = (
                props.get("REZ_NAME") or props.get("REZ_ID") or
                props.get("Name") or props.get("name") or
                props.get("ZONE_NAME") or props.get("LABEL") or "QLD REZ"
            )
            props["rez_name"] = str(name)
            props["state"] = "QLD"

    return geojson


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    print("=" * 60)
    print("Chapter 1.3 Step 12 - Fetch Renewable Energy Zone Data")
    print("=" * 60)

    results: dict[str, bool] = {}

    # VIC
    print("\n[1/4] Fetching VIC REZ polygons (VicGrid ArcGIS)...")
    vic_geojson = fetch_vic_rez()
    if vic_geojson and vic_geojson.get("features"):
        _save_geojson(vic_geojson, "VIC", "rez_vic.geojson")
        results["VIC"] = True
    else:
        print("  [VIC/REZ] WARNING: No data fetched - rez_vic.geojson not created.")
        results["VIC"] = False

    # TAS
    print("\n[2/4] Fetching TAS REZ polygons (State Growth ArcGIS)...")
    tas_geojson = fetch_tas_rez()
    if tas_geojson and tas_geojson.get("features"):
        _save_geojson(tas_geojson, "TAS", "rez_tas.geojson")
        results["TAS"] = True
    else:
        print("  [TAS/REZ] WARNING: No data fetched - rez_tas.geojson not created.")
        results["TAS"] = False

    # NSW
    print("\n[3/4] Fetching NSW REZ polygons (EnergyCo / data.nsw.gov.au)...")
    nsw_geojson = fetch_nsw_rez()
    if nsw_geojson and nsw_geojson.get("features"):
        _save_geojson(nsw_geojson, "NSW", "rez_nsw.geojson")
        results["NSW"] = True
    else:
        print("  [NSW/REZ] WARNING: No data fetched - rez_nsw.geojson not created.")
        results["NSW"] = False

    # QLD
    print("\n[4/4] Fetching QLD REZ polygons (Powerlink / data.qld.gov.au)...")
    qld_geojson = fetch_qld_rez()
    if qld_geojson and qld_geojson.get("features"):
        _save_geojson(qld_geojson, "QLD", "rez_qld.geojson")
        results["QLD"] = True
    else:
        print("  [QLD/REZ] WARNING: No data fetched - rez_qld.geojson not created.")
        results["QLD"] = False

    print("\n" + "=" * 60)
    print("REZ Fetch Summary:")
    for state, ok in results.items():
        status = "OK" if ok else "No data"
        print(f"  {state}: {status}")

    success_count = sum(results.values())
    print(f"\n  {success_count}/{len(results)} states fetched successfully.")
    if success_count == 0:
        print("  ERROR: No REZ data fetched at all.")
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
