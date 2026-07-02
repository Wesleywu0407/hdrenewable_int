"""Chapter 1.3 Step 8 - Generate infrastructure map charts.

Loads BESS and Datacentre CSV files and renders a combined Plotly
scatter-map of Australia, saved as:
  outputs/figures/fig1_4_infrastructure_map.html

Run: python -m scripts.chapter_1.generate_infrastructure_charts
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"
PNG_DIR = FIG_DIR / "png"
FIG_DIR.mkdir(parents=True, exist_ok=True)
PNG_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Colours
# --------------------------------------------------------------------------- #
BESS_COLOR = "#27ae60"          # green
BESS_COLOR_BORDER = "#1a7a44"
DC_COLOR = "#e74c3c"            # vivid red-orange - distinct from green BESS
DC_COLOR_BORDER = "#ffffff"     # white ring makes DCs pop over BESS markers



# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _status_label(status: str | None) -> str:
    """Normalise raw status string for display."""
    if not status or str(status).lower() in {"none", "nan"}:
        return "Unknown"
    s = str(status).strip().lower()
    if "operat" in s or "operating" in s:
        return "Operating"
    if "construct" in s or "building" in s or "under" in s:
        return "Under construction"
    if "commit" in s or "approved" in s or "financ" in s:
        return "Committed"
    if "plan" in s or "propos" in s:
        return "Proposed"
    if "decommission" in s or "retired" in s:
        return "Decommissioned"
    return str(status).strip().title()


def _capacity_to_size(cap: pd.Series, min_px: float = 3, max_px: float = 14) -> pd.Series:
    """Scale MW capacity to marker pixel sizes using sqrt scaling."""
    cap = pd.to_numeric(cap, errors="coerce").fillna(50)
    cap_sqrt = cap.clip(lower=1).pow(0.5)
    lo, hi = cap_sqrt.min(), cap_sqrt.max()
    if hi == lo:
        return pd.Series([min_px + (max_px - min_px) / 2] * len(cap))
    return min_px + (max_px - min_px) * (cap_sqrt - lo) / (hi - lo)


def save_html(fig: go.Figure, name: str) -> Path:
    path = FIG_DIR / name
    fig.write_html(path, include_plotlyjs="cdn", config={"scrollZoom": True, "displayModeBar": False, "displaylogo": False})
    print(f"  wrote {name} ({path.stat().st_size / 1024:.0f} KB)")
    return path


def save_png(fig: go.Figure, name: str, width: int = 1400, height: int = 900) -> None:
    try:
        png_path = PNG_DIR / name
        fig.write_image(png_path, width=width, height=height, scale=2)
        print(f"  wrote {name} ({png_path.stat().st_size / 1024:.0f} KB)")
    except Exception as exc:
        print(f"  [PNG] skipped ({type(exc).__name__}: {exc})")


# --------------------------------------------------------------------------- #
# Chart builder
# --------------------------------------------------------------------------- #

def build_infrastructure_map(bess_df: pd.DataFrame, dc_df: pd.DataFrame, solar_df: pd.DataFrame = None, selected_states: list[str] = None) -> go.Figure:
    """Build a combined Plotly Scattermapbox chart of BESS, Solar + Datacentres.

    Parameters
    ----------
    bess_df:   Battery storage site DataFrame
    dc_df:     Data centre DataFrame
    solar_df:  Solar farm DataFrame (optional)
    selected_states: List of states to display REZ for (optional)
    """
    fig = go.Figure()
    
    # Always add an empty trace to guarantee the mapbox tiles render when dataframes are empty
    fig.add_trace(go.Scattermapbox(lat=[None], lon=[None], showlegend=False, hoverinfo="skip"))

    # -- State Boundaries -------------------------------------------------------
    state_bounds_path = RAW_DIR / "australian_states.geojson"
    if state_bounds_path.exists():
        try:
            with open(state_bounds_path, encoding="utf-8") as f:
                state_data = json.load(f)
            
            lons, lats = [], []
            for feat in state_data.get("features", []):
                geom = feat.get("geometry", {})
                if not geom:
                    continue
                geom_type = geom.get("type")
                coords = geom.get("coordinates", [])
                
                def add_line(line_coords):
                    for pt in line_coords:
                        lons.append(pt[0])
                        lats.append(pt[1])
                    lons.append(None)
                    lats.append(None)
                    
                if geom_type == "Polygon":
                    for ring in coords:
                        add_line(ring)
                elif geom_type == "MultiPolygon":
                    for poly in coords:
                        for ring in poly:
                            add_line(ring)
                            
            if lons:
                fig.add_trace(go.Scattermapbox(
                    lon=lons, lat=lats,
                    mode='lines',
                    line=dict(color='rgba(255, 255, 255, 0.06)', width=1.5),
                    name='State Borders',
                    showlegend=False,
                    hoverinfo='skip'
                ))
            print("  [map] added State Borders.")
        except Exception as e:
            print(f"  [map/States] Failed to load {state_bounds_path.name}: {e}")

    # -- Renewable Energy Zone polygon overlays ---------------------------------
    # Load AEMO combined GeoJSON if present (to extract QLD and SA)
    aemo_features = []
    aemo_path = RAW_DIR / "aemo_res_all.geojson"
    if aemo_path.exists():
        try:
            with open(aemo_path, encoding="utf-8") as f:
                aemo_geojson = json.load(f)
                aemo_features = aemo_geojson.get("features", [])
        except Exception as e:
            print(f"  [map/REZ] Failed to load {aemo_path.name}: {e}")

    rez_legend_added = False
    for state in ["VIC", "TAS", "NSW", "QLD", "SA"]:
        if selected_states and state not in selected_states:
            continue

        geojson = {"type": "FeatureCollection", "features": []}
        
        # For VIC, TAS, NSW, prefer the state-specific files
        state_file = RAW_DIR / f"rez_{state.lower()}.geojson"
        if state_file.exists():
            try:
                with open(state_file, encoding="utf-8") as f:
                    geojson = json.load(f)
            except Exception as exc:
                print(f"  [map/REZ] Failed to load {state_file.name}: {exc}")
        elif aemo_features:
            # If no state-specific file, fall back to extracting from AEMO data
            state_features = []
            for feat in aemo_features:
                props = feat.get("properties", {})
                name = str(props.get("Name") or props.get("name") or "")
                
                if state == "QLD" and name.startswith("Q"):
                    state_features.append(feat)
                elif state == "SA" and name.startswith("S"):
                    # Exclude offshore zones
                    if "coast" not in name.lower() and "ocean" not in name.lower():
                        state_features.append(feat)
            
            geojson["features"] = state_features

        n_features = len(geojson.get("features", []))
        if n_features == 0:
            print(f"  [map/REZ] No data found for {state} - skipping.")
            continue

        lons, lats, hover_texts = [], [], []
        for feat in geojson["features"]:
            geom = feat.get("geometry", {})
            if not geom:
                continue
            props = feat.get("properties", {})
            geom_type = geom.get("type")
            coords = geom.get("coordinates", [])
            name = str(props.get("Name") or props.get("name") or "")
            
            def add_ring(ring, *, target_lons=lons, target_lats=lats, target_hover_texts=hover_texts, feature_name=name):
                for pt in ring:
                    target_lons.append(pt[0])
                    target_lats.append(pt[1])
                    target_hover_texts.append(feature_name)
                target_lons.append(None)
                target_lats.append(None)
                target_hover_texts.append(None)

            if geom_type == "Polygon":
                for ring in coords:
                    add_ring(ring)
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        add_ring(ring)
                        
        if lons:
            fig.add_trace(go.Scattermapbox(
                lon=lons, lat=lats,
                mode='lines',
                fill='toself',
                fillcolor='rgba(154, 160, 166, 0.1)',
                line=dict(color='rgba(154, 160, 166, 0.4)', width=2),
                name='REZ',
                legendgroup='REZ',
                showlegend=not rez_legend_added,
                hoverinfo='text',
                text=hover_texts
            ))
            rez_legend_added = True
        print(f"  [map/REZ] added {n_features} {state} REZ polygons.")

    # -- Transmission Lines ---------------------------------------------------
    tx_path = RAW_DIR / "transmission_lines_simplified.geojson"
    if tx_path.exists():
        try:
            with open(tx_path, encoding="utf-8") as f:
                tx_data = json.load(f)
            
            lons, lats = [], []
            for feat in tx_data.get("features", []):
                geom = feat.get("geometry", {})
                if not geom:
                    continue
                geom_type = geom.get("type")
                coords = geom.get("coordinates", [])
                
                def add_line(line_coords):
                    for pt in line_coords:
                        lons.append(pt[0])
                        lats.append(pt[1])
                    lons.append(None)
                    lats.append(None)
                    
                if geom_type == "LineString":
                    add_line(coords)
                elif geom_type == "MultiLineString":
                    for line in coords:
                        add_line(line)
                        
            if lons:
                fig.add_trace(go.Scattermapbox(
                    lon=lons, lat=lats,
                    mode='lines',
                    line=dict(color='rgba(64, 160, 255, 0.3)', width=1.5),
                    name='Transmission Grid',
                    showlegend=True,
                    hoverinfo='skip'
                ))
            print(f"  [map] added {len(tx_data.get('features', []))} transmission lines.")
        except Exception as e:
            print(f"  [map/TX] Failed to load {tx_path.name}: {e}")

    # -- BESS trace (drawn first = underneath) ------------------------------
    bess_hdre = None
    solar_hdre = None
    
    if not bess_df.empty:
        bess_valid = bess_df.dropna(subset=["lat", "lon"]).copy()
        if not bess_valid.empty:
            bess_valid["status_lower"] = bess_valid["status"].fillna("").astype(str).str.lower()
            existing_mask = bess_valid["status_lower"].isin(["operating", "commissioning"])
            hdre_mask = bess_valid["source"] == "HDRE/ZEBRE Verified Data"
            
            bess_hdre = bess_valid[hdre_mask]
            bess_existing = bess_valid[existing_mask & ~hdre_mask]
            bess_proposed = bess_valid[~existing_mask & ~hdre_mask]

            for subset_df, color, name_label, border_color, lg, lg_title in [
                (bess_existing, BESS_COLOR, "BESS", BESS_COLOR_BORDER, "current", "Current Sites"),
                (bess_proposed, "#9b59b6", "BESS", "#5e3370", "proposed", "Proposed Sites")
            ]:
                if subset_df.empty:
                    continue
                sizes = _capacity_to_size(subset_df["capacity_mw"])

                # Build hover text
                hover_texts = []
                for _, row in subset_df.iterrows():
                    cap = row.get("capacity_mw")
                    cap_str = f"{cap:,.0f} MW" if pd.notna(cap) and cap else "Unknown"
                    status = _status_label(row.get("status", ""))
                    state = row.get("state", "")
                    source = row.get("source", "")
                    hover_texts.append(
                        f"<b>{row['name']}</b><br>"
                        f"Capacity: {cap_str}<br>"
                        f"Status: {status}<br>"
                        f"State: {state}<br>"
                        f"<i>Source: {source}</i>"
                    )

                # Border trace
                fig.add_trace(
                    go.Scattermapbox(
                        lat=subset_df["lat"],
                        lon=subset_df["lon"],
                        mode="markers",
                        marker=dict(
                            size=sizes + 3,
                            color=border_color,
                            opacity=0.7,
                        ),
                        text=subset_df["name"].tolist(),
                        hoverinfo="skip",
                        showlegend=False,
                        legendgroup=lg,
                    )
                )
                # Fill trace
                fig.add_trace(
                    go.Scattermapbox(
                        lat=subset_df["lat"],
                        lon=subset_df["lon"],
                        mode="markers",
                        marker=dict(
                            size=sizes,
                            color=color,
                            opacity=0.5,
                        ),
                        text=hover_texts,
                        hovertemplate="%{text}<extra></extra>",
                        name=name_label,
                        legendgroup=lg,
                        legendgrouptitle_text=lg_title,
                    )
                )
                print(f"  [map] added {len(subset_df)} {name_label.strip('🔋🏗️ ')} markers")

    # -- Solar trace --------------------------------------------------------
    if solar_df is not None and not solar_df.empty:
        solar_valid = solar_df.dropna(subset=["lat", "lon"]).copy()
        if not solar_valid.empty:
            solar_valid["status_lower"] = solar_valid["status"].fillna("").astype(str).str.lower()
            hdre_mask = solar_valid["source"] == "HDRE/ZEBRE Verified Data"
            solar_hdre = solar_valid[hdre_mask]
            solar_existing = solar_valid[solar_valid["status_lower"].isin(["operating", "commissioning"]) & ~hdre_mask]
            solar_proposed = solar_valid[~solar_valid["status_lower"].isin(["operating", "commissioning"]) & ~hdre_mask]
            
            for subset_df, color, name_label, border_color, lg, lg_title in [
                (solar_existing, "#FFD700", "Solar Panels", "#b8860b", "current", "Current Sites"),
                (solar_proposed, "#ff8833", "Solar Panels", "#cc6600", "proposed", "Proposed Sites")
            ]:
                if subset_df.empty:
                    continue
                sizes = _capacity_to_size(subset_df["capacity_mw"])
                hover_texts = []
                for _, row in subset_df.iterrows():
                    cap = row.get("capacity_mw")
                    cap_str = f"{cap:,.0f} MW" if pd.notna(cap) and cap else "Unknown"
                    status = _status_label(row.get("status", ""))
                    state = row.get("state", "")
                    source = row.get("source", "")
                    hover_texts.append(
                        f"<b>{row['name']}</b><br>"
                        f"Capacity: {cap_str}<br>"
                        f"Status: {status}<br>"
                        f"State: {state}<br>"
                        f"<i>Source: {source}</i>"
                    )

                # Border trace
                fig.add_trace(
                    go.Scattermapbox(
                        lat=subset_df["lat"],
                        lon=subset_df["lon"],
                        mode="markers",
                        marker=dict(
                            size=sizes + 3,
                            color=border_color,
                            opacity=0.7,
                        ),
                        text=subset_df["name"].tolist(),
                        hoverinfo="skip",
                        showlegend=False,
                        legendgroup=lg,
                    )
                )
                # Fill trace
                fig.add_trace(
                    go.Scattermapbox(
                        lat=subset_df["lat"],
                        lon=subset_df["lon"],
                        mode="markers",
                        marker=dict(
                            size=sizes,
                            color=color,
                            opacity=0.5,
                        ),
                        text=hover_texts,
                        hovertemplate="%{text}<extra></extra>",
                        name=name_label,
                        legendgroup=lg,
                        legendgrouptitle_text=lg_title,
                    )
                )
                clean_label = name_label.replace("☀️", "").replace("🏗️", "").replace("⚡", "").strip()
                print(f"  [map] added {len(subset_df)} {clean_label} markers")

    # -- Datacentre trace ---------------------------------------------------
    if not dc_df.empty:
        dc_valid = dc_df.dropna(subset=["lat", "lon"]).copy()
        if not dc_valid.empty:
            hover_texts = []
            for _, row in dc_valid.iterrows():
                provider = row.get("provider", "")
                city = row.get("city", "")
                source = row.get("source", "")
                hover_texts.append(
                    f"<b>{row['name']}</b><br>"
                    f"Provider: {provider or 'N/A'}<br>"
                    f"City: {city or 'N/A'}<br>"
                    f"<i>Source: {source}</i>"
                )

            # Two-pass approach for white border ring effect:
            # 1. Slightly larger white circle underneath (border)
            # 2. Red circle on top (fill)
            # scattermapbox Marker has no `line` property, so we fake a border.
            fig.add_trace(
                go.Scattermapbox(
                    lat=dc_valid["lat"],
                    lon=dc_valid["lon"],
                    mode="markers",
                    marker=dict(size=10, color="#ffffff", opacity=0.8),
                    text=dc_valid["name"].tolist(),
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup="dc",
                )
            )
            fig.add_trace(
                go.Scattermapbox(
                    lat=dc_valid["lat"],
                    lon=dc_valid["lon"],
                    mode="markers",
                    marker=dict(size=7, color=DC_COLOR, opacity=0.8),
                    text=hover_texts,
                    hovertemplate="%{text}<extra></extra>",
                    name="Data Centres",
                    legendgroup="dc",
                    legendgrouptitle_text="Data Centres",
                )
            )
            print(f"  [map] added {len(dc_valid)} Datacentre markers")

    # -- Overlaid HDRE/ZEBRE traces (drawn last = on top) -------------------
    hdre_curr_pattern = r"(?i)(?:Solar River|Wagga North|Templers)"

    hdre_frames = []
    if bess_hdre is not None and not bess_hdre.empty:
        b_hdre = bess_hdre.copy()
        b_hdre["asset_type"] = "Battery (BESS)"
        hdre_frames.append(b_hdre)
    if solar_hdre is not None and not solar_hdre.empty:
        s_hdre = solar_hdre.copy()
        s_hdre["asset_type"] = "Solar Farm"
        hdre_frames.append(s_hdre)

    if hdre_frames:
        import re
        combined_hdre = pd.concat(hdre_frames, ignore_index=True)
        grouped_hdre = []
        for name_tuple, group in combined_hdre.groupby(['name', 'lat', 'lon', 'status', 'state', 'source'], dropna=False):
            total_cap = group['capacity_mw'].sum()
            assets = []
            for _, r in group.iterrows():
                cap_str = f"{r['capacity_mw']:,.0f} MW" if pd.notna(r['capacity_mw']) and r['capacity_mw'] else "Unknown"
                assets.append(f"{r['asset_type']}: {cap_str}")
            
            asset_desc = " + ".join([r['asset_type'].split()[0] for _, r in group.iterrows()])
            if len(group) > 1:
                site_type_label = "Hybrid Site"
            else:
                site_type_label = asset_desc

            is_curr = bool(re.search(hdre_curr_pattern, str(name_tuple[0])))
            zebre_status = "Current" if is_curr else "Seeking"

            hover_txt = (
                f"<b>{name_tuple[0]}</b><br>"
                f"Type: {site_type_label}<br>"
                f"{'<br>'.join(assets)}<br>"
                f"Status: <b>{zebre_status}</b><br>"
                f"State: {name_tuple[4]}<br>"
                f"<i>Source: {name_tuple[5]}</i>"
            )
            
            grouped_hdre.append({
                'name': name_tuple[0],
                'lat': name_tuple[1],
                'lon': name_tuple[2],
                'total_cap': total_cap,
                'hover_text': hover_txt,
                'is_curr': is_curr
            })
            
        merged_hdre_df = pd.DataFrame(grouped_hdre)
        
        if not merged_hdre_df.empty:
            sizes = _capacity_to_size(merged_hdre_df["total_cap"])
            b_op_list = [1.0] * len(merged_hdre_df)
            f_op_list = [1.0 if c else 0.5 for c in merged_hdre_df['is_curr']]

            # Border trace
            fig.add_trace(
                go.Scattermapbox(
                    lat=merged_hdre_df["lat"],
                    lon=merged_hdre_df["lon"],
                    mode="markers",
                    marker=dict(
                        size=sizes + 2,
                        color="white",
                        opacity=b_op_list,
                    ),
                    text=merged_hdre_df["name"].tolist(),
                    hoverinfo="skip",
                    showlegend=False,
                    legendgroup="hdre_combined",
                )
            )
            # Fill trace
            fig.add_trace(
                go.Scattermapbox(
                    lat=merged_hdre_df["lat"],
                    lon=merged_hdre_df["lon"],
                    mode="markers",
                    marker=dict(
                        size=sizes - 1,
                        color="#00d2ff",
                        opacity=f_op_list,
                    ),
                    text=merged_hdre_df["hover_text"].tolist(),
                    hovertemplate="%{text}<extra></extra>",
                    name="HDRE Projects",
                    legendgroup="hdre_combined",
                    legendgrouptitle_text="HDRE Projects",
                )
            )
            print(f"  [map] added {len(merged_hdre_df)} combined ZEBRE markers (OVERLAID)")


    # -- Layout -------------------------------------------------------------
    mapbox_config = dict(
        style="carto-darkmatter",
        center=dict(lat=-25.27, lon=133.77),
        zoom=3.5,
    )

    fig.update_layout(
        # scattermapbox requires the `mapbox` key (not `map`)
        # and works reliably with the CDN-hosted plotly.js bundle.
        mapbox=mapbox_config,
        legend=dict(
            orientation="v",
            x=0.01,
            y=0.99,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(26, 26, 38, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.2)",
            borderwidth=1,
            font=dict(size=13, color="#e2e8f0"),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=750,
        paper_bgcolor="#f4f6f8",
    )



    return fig


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    print("Generating infrastructure map → outputs/figures/")

    bess_path = RAW_DIR / "bess_locations.csv"
    dc_path = RAW_DIR / "datacentre_locations.csv"
    solar_path = RAW_DIR / "solar_locations.csv"

    if not bess_path.exists():
        print(f"WARNING: {bess_path} not found - run python -m scripts.chapter_1.fetch_infrastructure_data first.")
        bess_df = pd.DataFrame()
    else:
        bess_df = pd.read_csv(bess_path)
        print(f"  loaded bess_locations.csv: {len(bess_df)} rows")

    if not dc_path.exists():
        print(f"WARNING: {dc_path} not found - run python -m scripts.chapter_1.fetch_infrastructure_data first.")
        dc_df = pd.DataFrame()
    else:
        dc_df = pd.read_csv(dc_path)
        print(f"  loaded datacentre_locations.csv: {len(dc_df)} rows")

    if not solar_path.exists():
        print(f"WARNING: {solar_path} not found.")
        solar_df = pd.DataFrame()
    else:
        solar_df = pd.read_csv(solar_path)
        print(f"  loaded solar_locations.csv: {len(solar_df)} rows")

    if bess_df.empty and dc_df.empty and solar_df.empty:
        print("ERROR: No data available to plot.")
        return 1

    fig = build_infrastructure_map(bess_df, dc_df, solar_df)
    save_html(fig, "fig1_4_infrastructure_map.html")
    save_png(fig, "fig1_4_infrastructure_map.png")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
