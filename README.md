 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index 1693c3b5e51f86fb35bc33e1211ffad1f3a8f2a4..9f3ec8b1f61b0c03c316fb0c927b0fb1d3aaba1b 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,91 @@
-# BTC_XRP
+# XRP vs BTC Normalized Growth App
+
+This project provides a Streamlit dashboard that compares the long-run performance of Bitcoin (BTC) and XRP. It fetches daily historical prices from CoinGecko, aligns the overlapping history, computes indexed growth metrics, and renders charts and exports for deeper analysis.
+
+## Features
+
+- Fetches full historical price data for BTC and XRP (with caching to avoid excessive API calls).
+- Aligns series by earliest overlapping date and supports resampling to daily, weekly, or monthly frequency.
+- Computes indexed growth, CAGR, XRP/BTC ratio, z-scores (price or log-price), optional rolling CAGR, and drawdowns.
+- Streamlit UI with sidebar controls for frequency, z-score mode, rolling window, rebase date, and drawdown chart toggle.
+- Exports CSV, PNG charts, and a text summary to the `exports/` directory with
+  in-app download buttons for Streamlit Cloud deployments.
+- Unit tests covering alignment, CAGR calculations, z-score normalization, and ratio identity.
+
+## Project Structure
+
+```
+.
+├── app.py
+├── core
+│   ├── __init__.py
+│   ├── charts.py
+│   ├── compute.py
+│   └── data_source.py
+├── data
+│   └── .gitkeep
+├── exports
+│   └── .gitkeep
+├── requirements.txt
+└── tests
+    ├── test_alignment.py
+    └── test_compute.py
+```
+
+## Getting Started
+
+1. **Create and activate a virtual environment (Python 3.11+ recommended):**
+
+   ```bash
+   python3 -m venv .venv
+   source .venv/bin/activate
+   ```
+
+2. **Install dependencies:**
+
+   ```bash
+   pip install --upgrade pip
+   pip install -r requirements.txt
+   ```
+
+3. **Run the Streamlit app:**
+
+   ```bash
+   streamlit run app.py
+   ```
+
+   The app fetches BTC and XRP data from CoinGecko. The first load may take a few seconds while data is fetched and cached under `data/`.
+
+4. **Use the dashboard:**
+   - Adjust frequency, rolling window, z-score mode, and drawdown toggle in the sidebar.
+   - Choose a rebase date (defaults to earliest overlapping date).
+   - Click **Fetch & Compute** to update calculations.
+   - Use the download buttons to retrieve the CSV or a ZIP archive containing
+     charts and the summary (also written to `exports/`).
+
+5. **Run tests:**
+
+   ```bash
+   pytest
+   ```
+
+## Exports
+
+When the download buttons are used, the following files are written to `exports/`
+and included in the downloadable ZIP archive:
+
+- `xrp_btc_full_series.csv`
+- `01_indexed_growth.png`
+- `02_ratio_xrp_btc.png`
+- `03_zscores.png`
+- `04_drawdowns.png` (if drawdown chart enabled)
+- `summary.txt`
+
+## Notes
+
+- API responses are cached for 24 hours in `data/cache_{coin}.json` to minimize repeated calls.
+- Ensure an active internet connection when fetching data the first time. Subsequent runs within the cache window reuse local data.
+
+## License
+
+This project is provided under the MIT License.
 
EOF
)
