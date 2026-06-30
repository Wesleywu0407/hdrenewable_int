import os
from script2stlite.functions import create_html, write_text_file, load_all_versions

import sys
sys.path.insert(0, os.path.abspath("."))

from dashboard.config import CHAPTERS

directory = "."
app_files = [
    "dashboard/app.py",
    "dashboard/config.py",
    "dashboard/styles.py"
]

for chapter in CHAPTERS:
    for figure in chapter.get("figures", []):
        html_path = figure.get("html_path")
        if html_path and os.path.exists(html_path) and html_path not in app_files:
            app_files.append(html_path)
        png_path = figure.get("png_path")
        if png_path and os.path.exists(png_path) and png_path not in app_files:
            app_files.append(png_path)


css_vers, top_css, js_vers, top_js, pyo_vers, top_pyo = load_all_versions()

settings = {
    "APP_NAME": "HDRE_NEM_Dashboard",
    "APP_ENTRYPOINT": "dashboard/app.py",
    "APP_REQUIREMENTS": ["streamlit>=1.32", "pandas", "plotly"],
    "APP_FILES": app_files,
    "|STLITE_CSS|": top_css,
    "|STLITE_JS|": top_js,
    "|PYODIDE_VERSION|": top_pyo,
    "CONFIG": "missing.toml"
}

print(f"Bundling {len(app_files)} files into single HTML...")
html = create_html(directory, settings)
write_text_file("dashboard_exported.html", html)
print("Export complete: dashboard_exported.html")
