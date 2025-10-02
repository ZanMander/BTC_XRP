 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/app.py
index 0000000000000000000000000000000000000000..e90c1683603039531249c486eac4b8194c6b5892 100644
--- a//dev/null
+++ b/app.py
@@ -0,0 +1,220 @@
+"""Streamlit application for comparing XRP and BTC performance."""
+from __future__ import annotations
+
+import time
+import zipfile
+from datetime import date
+from io import BytesIO
+from pathlib import Path
+from typing import Dict, Optional
+
+import pandas as pd
+import streamlit as st
+
+from core.charts import plot_drawdown, plot_indexed_growth, plot_ratio, plot_zscores
+from core.compute import compute
+from core.data_source import fetch_market_chart
+
+EXPORT_DIR = Path("exports")
+EXPORT_DIR.mkdir(parents=True, exist_ok=True)
+
+
+st.set_page_config(page_title="XRP vs BTC Analysis", layout="wide")
+st.title("XRP vs BTC Normalized Growth")
+st.caption("Fetch data from CoinGecko, align histories, and compare indexed performance.")
+
+
+@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
+def load_coin_data(coin_id: str) -> pd.DataFrame:
+    return fetch_market_chart(coin_id)
+
+
+def determine_overlap(
+    btc_df: pd.DataFrame, xrp_df: pd.DataFrame
+) -> tuple[date, date]:
+    start = max(btc_df["date"].min(), xrp_df["date"].min()).date()
+    end = min(btc_df["date"].max(), xrp_df["date"].max()).date()
+    return start, end
+
+
+if "results_df" not in st.session_state:
+    st.session_state["results_df"] = None
+if "summary" not in st.session_state:
+    st.session_state["summary"] = None
+
+with st.sidebar:
+    st.header("Controls")
+    try:
+        btc_raw = load_coin_data("bitcoin")
+        time.sleep(1.05)
+        xrp_raw = load_coin_data("ripple")
+    except Exception as exc:  # pragma: no cover - UI handling
+        st.error(f"Failed to load initial data: {exc}")
+        st.stop()
+
+    overlap_start, overlap_end = determine_overlap(btc_raw, xrp_raw)
+
+    frequency_label = st.selectbox(
+        "Frequency",
+        options=["Monthly", "Weekly", "Daily"],
+        index=0,
+    )
+    frequency_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
+    frequency = frequency_map[frequency_label]
+
+    z_log = st.checkbox("Use log-prices for z-scores", value=False)
+
+    rolling_label = st.selectbox(
+        "Rolling window (days)",
+        options=["None", "90", "180", "365"],
+        index=0,
+    )
+    rolling_days: Optional[int]
+    if rolling_label == "None":
+        rolling_days = None
+    else:
+        rolling_days = int(rolling_label)
+
+    include_drawdown = st.checkbox("Include drawdown chart", value=False)
+
+    rebase_date_input = st.date_input(
+        "Rebase date",
+        value=overlap_start,
+        min_value=overlap_start,
+        max_value=overlap_end,
+    )
+
+    fetch_button = st.button("Fetch & Compute", use_container_width=True)
+
+if fetch_button:
+    with st.spinner("Fetching data and computing metrics..."):
+        try:
+            results_df, summary = compute(
+                btc_raw,
+                xrp_raw,
+                frequency=frequency,
+                rebase_date=pd.Timestamp(rebase_date_input),
+                z_log=z_log,
+                rolling_days=rolling_days,
+                include_drawdown=include_drawdown,
+            )
+            st.session_state["results_df"] = results_df
+            st.session_state["summary"] = summary
+        except Exception as exc:  # pragma: no cover - UI handling
+            st.error(f"Error during computation: {exc}")
+
+results_df: Optional[pd.DataFrame] = st.session_state.get("results_df")
+summary: Optional[Dict[str, object]] = st.session_state.get("summary")
+
+if results_df is not None and summary is not None:
+    st.subheader("Summary")
+    cols = st.columns(3)
+    start_dt = summary["start_date"]
+    end_dt = summary["end_date"]
+    span_years = summary["span_years"]
+    btc_cagr = summary["btc_cagr"]
+    xrp_cagr = summary["xrp_cagr"]
+
+    cols[0].metric("Start Date", pd.to_datetime(start_dt).strftime("%Y-%m-%d"))
+    cols[1].metric("End Date", pd.to_datetime(end_dt).strftime("%Y-%m-%d"))
+    cols[2].metric("Span (years)", f"{span_years:.2f}")
+
+    price_cols = st.columns(4)
+    price_cols[0].metric("BTC Start", f"${summary['btc_start_price']:.2f}")
+    price_cols[1].metric("BTC End", f"${summary['btc_end_price']:.2f}")
+    price_cols[2].metric("XRP Start", f"${summary['xrp_start_price']:.4f}")
+    price_cols[3].metric("XRP End", f"${summary['xrp_end_price']:.4f}")
+
+    growth_cols = st.columns(3)
+    growth_cols[0].metric("BTC CAGR", f"{btc_cagr * 100:.2f}%")
+    growth_cols[1].metric("XRP CAGR", f"{xrp_cagr * 100:.2f}%")
+    growth_cols[2].metric(
+        "XRP/BTC Ratio",
+        f"{summary['ratio_start']:.4f} → {summary['ratio_end']:.4f}",
+    )
+
+    st.markdown("---")
+
+    chart_df = results_df.copy()
+    fig_index = plot_indexed_growth(chart_df, save=False)
+    st.pyplot(fig_index)
+
+    fig_ratio = plot_ratio(chart_df, save=False)
+    st.pyplot(fig_ratio)
+
+    fig_z = plot_zscores(chart_df, save=False)
+    st.pyplot(fig_z)
+
+    drawdown_fig = plot_drawdown(chart_df, save=False)
+    if drawdown_fig is not None:
+        st.pyplot(drawdown_fig)
+
+    st.subheader("Data Preview")
+    st.dataframe(chart_df.tail(200), use_container_width=True)
+
+    export_col1, export_col2 = st.columns(2)
+
+    csv_bytes = chart_df.to_csv(index=False).encode("utf-8")
+    csv_path = EXPORT_DIR / "xrp_btc_full_series.csv"
+    csv_path.write_bytes(csv_bytes)
+    export_col1.download_button(
+        "Download CSV",
+        data=csv_bytes,
+        file_name="xrp_btc_full_series.csv",
+        mime="text/csv",
+        use_container_width=True,
+    )
+
+    plot_indexed_growth(chart_df, save=True)
+    plot_ratio(chart_df, save=True)
+    plot_zscores(chart_df, save=True)
+    if include_drawdown:
+        plot_drawdown(chart_df, save=True)
+
+    summary_lines = [
+        "XRP vs BTC Summary",
+        "====================",
+        f"Start Date: {pd.to_datetime(start_dt).strftime('%Y-%m-%d')}",
+        f"End Date: {pd.to_datetime(end_dt).strftime('%Y-%m-%d')}",
+        f"Span (years): {span_years:.2f}",
+        f"BTC CAGR: {btc_cagr * 100:.2f}%",
+        f"XRP CAGR: {xrp_cagr * 100:.2f}%",
+        f"XRP/BTC Ratio Start: {summary['ratio_start']:.4f}",
+        f"XRP/BTC Ratio End: {summary['ratio_end']:.4f}",
+        f"Frequency: {frequency_label}",
+        f"Rolling Window: {rolling_label}",
+        f"Z-Scores via Log Prices: {'Yes' if z_log else 'No'}",
+    ]
+    summary_text = "\n".join(summary_lines)
+    summary_path = EXPORT_DIR / "summary.txt"
+    summary_path.write_text(summary_text, encoding="utf-8")
+
+    chart_files = {
+        "01_indexed_growth.png": fig_index,
+        "02_ratio_xrp_btc.png": fig_ratio,
+        "03_zscores.png": fig_z,
+    }
+    if include_drawdown and drawdown_fig is not None:
+        chart_files["04_drawdowns.png"] = drawdown_fig
+
+    zip_buffer = BytesIO()
+    with zipfile.ZipFile(zip_buffer, "w") as archive:
+        for filename, figure in chart_files.items():
+            image_buffer = BytesIO()
+            figure.savefig(image_buffer, format="png", dpi=150)
+            archive.writestr(filename, image_buffer.getvalue())
+        archive.writestr("summary.txt", summary_text)
+        archive.writestr("xrp_btc_full_series.csv", csv_bytes)
+    zip_buffer.seek(0)
+
+    export_col2.download_button(
+        "Download Charts & Summary (ZIP)",
+        data=zip_buffer.getvalue(),
+        file_name="xrp_btc_artifacts.zip",
+        mime="application/zip",
+        use_container_width=True,
+    )
+
+    st.caption("Artifacts are saved to the exports/ directory and available for download above.")
+else:
+    st.info("Use the sidebar controls and click 'Fetch & Compute' to load the analysis.")
 
EOF
)
