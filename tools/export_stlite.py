"""Bundle the Streamlit dashboard into a single stlite HTML file."""

from __future__ import annotations

import sys
from pathlib import Path

from script2stlite.functions import create_html, load_all_versions, write_text_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import CHAPTERS  # noqa: E402


def add_existing(app_files: list[str], path: Path) -> None:
    """Add a project-relative file path once when it exists."""
    if path.is_file():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel not in app_files:
            app_files.append(rel)


def collect_app_files() -> list[str]:
    """Collect dashboard, pipeline, data, runtime, and figure files for stlite."""
    app_files: list[str] = []

    for folder in ["dashboard", "scripts"]:
        for path in sorted((PROJECT_ROOT / folder).rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if path.suffix in {".py", ".sh", ".css"}:
                add_existing(app_files, path)

    for rel_path in [
        "data/raw/bess_locations.csv",
        "data/raw/solar_locations.csv",
        "data/raw/datacentre_locations.csv",
        "data/raw/transmission_lines_simplified.geojson",
        "data/raw/rez_nsw.geojson",
        "data/raw/rez_vic.geojson",
        "data/raw/rez_tas.geojson",
        "data/raw/aemo_res_all.geojson",
    ]:
        add_existing(app_files, PROJECT_ROOT / rel_path)

    for folder in ["runtime/refresh", "logs"]:
        for path in sorted((PROJECT_ROOT / folder).glob("*")):
            add_existing(app_files, path)

    for chapter in CHAPTERS:
        for figure in chapter.get("figures", []):
            for key in ["html_path", "png_path"]:
                rel_path = figure.get(key)
                if rel_path:
                    add_existing(app_files, PROJECT_ROOT / rel_path)

    return app_files


def main() -> int:
    css_vers, top_css, js_vers, top_js, pyo_vers, top_pyo = load_all_versions()
    app_files = collect_app_files()
    settings = {
        "APP_NAME": "HDRE_NEM_Dashboard",
        "APP_ENTRYPOINT": "dashboard/app.py",
        "APP_REQUIREMENTS": ["streamlit>=1.32", "pandas", "plotly"],
        "APP_FILES": app_files,
        "|STLITE_CSS|": top_css,
        "|STLITE_JS|": top_js,
        "|PYODIDE_VERSION|": top_pyo,
        "CONFIG": ".streamlit/config.toml",
    }

    print(f"Bundling {len(app_files)} files into single HTML...")
    html = create_html(str(PROJECT_ROOT), settings)
    write_text_file("dashboard_exported.html", html)
    print("Export complete: dashboard_exported.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
