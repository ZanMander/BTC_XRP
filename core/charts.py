 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/core/charts.py
index 0000000000000000000000000000000000000000..94b881fb4358f02b9ba910b6a389896bf384fc37 100644
--- a//dev/null
+++ b/core/charts.py
@@ -0,0 +1,100 @@
+"""Charting helpers for XRP vs BTC analysis."""
+from __future__ import annotations
+
+from pathlib import Path
+from typing import Optional
+
+import matplotlib.pyplot as plt
+import pandas as pd
+
+EXPORT_DIR = Path("exports")
+EXPORT_DIR.mkdir(parents=True, exist_ok=True)
+
+
+def _configure_style() -> None:
+    """Configure matplotlib style with graceful fallback."""
+
+    try:
+        plt.style.use("seaborn-v0_8")
+    except OSError:
+        plt.style.use("seaborn")
+    except Exception:
+        plt.style.use("default")
+
+
+def plot_indexed_growth(df: pd.DataFrame, save: bool = False) -> plt.Figure:
+    _configure_style()
+    fig, ax = plt.subplots(figsize=(10, 6))
+    ax.plot(df["date"], df["btc_indexed"], label="BTC Indexed", color="tab:blue")
+    ax.plot(df["date"], df["xrp_indexed"], label="XRP Indexed", color="tab:orange")
+    ax.set_title("Indexed Growth (Rebased = 1.0)")
+    ax.set_ylabel("Index Level")
+    ax.set_xlabel("Date")
+    ax.legend()
+    ax.grid(True, alpha=0.3)
+    fig.tight_layout()
+    if save:
+        fig_path = EXPORT_DIR / "01_indexed_growth.png"
+        fig.savefig(fig_path, dpi=150)
+    return fig
+
+
+def plot_ratio(df: pd.DataFrame, save: bool = False) -> plt.Figure:
+    _configure_style()
+    fig, ax = plt.subplots(figsize=(10, 4))
+    ax.plot(df["date"], df["xrp_btc_ratio"], label="XRP/BTC Ratio", color="tab:green")
+    ax.set_title("XRP/BTC Ratio")
+    ax.set_ylabel("Ratio")
+    ax.set_xlabel("Date")
+    ax.legend()
+    ax.grid(True, alpha=0.3)
+    fig.tight_layout()
+    if save:
+        fig_path = EXPORT_DIR / "02_ratio_xrp_btc.png"
+        fig.savefig(fig_path, dpi=150)
+    return fig
+
+
+def plot_zscores(df: pd.DataFrame, save: bool = False) -> plt.Figure:
+    _configure_style()
+    fig, ax = plt.subplots(figsize=(10, 4))
+    ax.plot(df["date"], df["btc_z"], label="BTC Z-Score", color="tab:purple")
+    ax.plot(df["date"], df["xrp_z"], label="XRP Z-Score", color="tab:red")
+    ax.set_title("Z-Scores (Price Levels)")
+    ax.set_ylabel("Z-Score")
+    ax.set_xlabel("Date")
+    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
+    ax.legend()
+    ax.grid(True, alpha=0.3)
+    fig.tight_layout()
+    if save:
+        fig_path = EXPORT_DIR / "03_zscores.png"
+        fig.savefig(fig_path, dpi=150)
+    return fig
+
+
+def plot_drawdown(df: pd.DataFrame, save: bool = False) -> Optional[plt.Figure]:
+    if "btc_drawdown" not in df.columns or "xrp_drawdown" not in df.columns:
+        return None
+    _configure_style()
+    fig, ax = plt.subplots(figsize=(10, 4))
+    ax.plot(df["date"], df["btc_drawdown"], label="BTC Drawdown", color="tab:blue")
+    ax.plot(df["date"], df["xrp_drawdown"], label="XRP Drawdown", color="tab:orange")
+    ax.set_title("Drawdowns")
+    ax.set_ylabel("Drawdown")
+    ax.set_xlabel("Date")
+    ax.legend()
+    ax.grid(True, alpha=0.3)
+    fig.tight_layout()
+    if save:
+        fig_path = EXPORT_DIR / "04_drawdowns.png"
+        fig.savefig(fig_path, dpi=150)
+    return fig
+
+
+__all__ = [
+    "plot_indexed_growth",
+    "plot_ratio",
+    "plot_zscores",
+    "plot_drawdown",
+]
 
EOF
)
