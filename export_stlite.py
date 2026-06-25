import os
from script2stlite.functions import create_html, write_text_file, load_all_versions

directory = "."
app_files = []

exclude_dirs = {".venv", ".git", "nemosis_cache", "venv", "__pycache__", ".streamlit"}

for root, dirs, files in os.walk(directory):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith((".py", ".csv", ".html", ".png", ".toml", ".md")):
            filepath = os.path.relpath(os.path.join(root, file), directory)
            if filepath != "dashboard/app.py" and filepath != "export_stlite.py":
                app_files.append(filepath)

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
