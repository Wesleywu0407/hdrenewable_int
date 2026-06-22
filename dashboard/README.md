# HDRE NEM research dashboard

Streamlit presentation layer for the HDRE Australia NEM research figures. The app embeds the existing Plotly HTML files from `outputs/figures/` and does not regenerate chart data.

## Run locally

From the project root:

```bash
uv pip install -r requirements.txt
streamlit run dashboard/app.py
```

If you are using the local virtual environment directly:

```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

## Add a figure

Edit `dashboard/config.py` and add a new figure entry under the relevant chapter:

```python
{
    "id": "fig6",
    "number": 6,
    "title": "New figure title",
    "subtitle": "新圖表副標",
    "html_path": "outputs/figures/new_figure.html",
    "png_path": "outputs/figures/new_figure.png",
    "metrics": [
        {"label": "Metric", "value": "123"},
    ],
    "takeaway": "One concise takeaway for stakeholders.",
}
```

Restart Streamlit after editing the config. No UI code changes are needed.

## Chapter status

Use `status` in `dashboard/config.py` to control sidebar state:

```python
"status": "done"     # active chapter with figures
"status": "wip"      # visible roadmap item
"status": "planned"  # visible roadmap item
```
