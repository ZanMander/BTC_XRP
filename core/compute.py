 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/core/compute.py
index 0000000000000000000000000000000000000000..286a6f24073201e3f4f893d585c8dc2dfe87ff01 100644
--- a//dev/null
+++ b/core/compute.py
@@ -0,0 +1,209 @@
+"""Computation utilities for XRP vs BTC analysis."""
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import datetime
+from typing import Dict, Optional, Tuple
+
+import numpy as np
+import pandas as pd
+
+
+@dataclass
+class Summary:
+    start_date: datetime
+    end_date: datetime
+    span_years: float
+    btc_start_price: float
+    btc_end_price: float
+    xrp_start_price: float
+    xrp_end_price: float
+    btc_cagr: float
+    xrp_cagr: float
+    ratio_start: float
+    ratio_end: float
+
+    def to_dict(self) -> Dict[str, float]:
+        return {
+            "start_date": self.start_date,
+            "end_date": self.end_date,
+            "span_years": self.span_years,
+            "btc_start_price": self.btc_start_price,
+            "btc_end_price": self.btc_end_price,
+            "xrp_start_price": self.xrp_start_price,
+            "xrp_end_price": self.xrp_end_price,
+            "btc_cagr": self.btc_cagr,
+            "xrp_cagr": self.xrp_cagr,
+            "ratio_start": self.ratio_start,
+            "ratio_end": self.ratio_end,
+        }
+
+
+def calculate_cagr(start_price: float, end_price: float, years: float) -> float:
+    if start_price <= 0 or end_price <= 0 or years <= 0:
+        return float("nan")
+    return (end_price / start_price) ** (1.0 / years) - 1.0
+
+
+def compute_drawdown(series: pd.Series) -> pd.Series:
+    running_max = series.cummax()
+    drawdown = series / running_max - 1.0
+    return drawdown
+
+
+def _estimate_period_days(index: pd.DatetimeIndex) -> float:
+    if len(index) < 2:
+        return 1.0
+    diffs = index.to_series().diff().dropna().dt.total_seconds() / 86400.0
+    if diffs.empty:
+        return 1.0
+    return float(diffs.median())
+
+
+def compute_z_scores(series: pd.Series, use_log: bool = False) -> pd.Series:
+    values = np.log(series) if use_log else series
+    mean = values.mean()
+    std = values.std(ddof=0)
+    if std == 0:
+        return pd.Series(np.nan, index=series.index)
+    z = (values - mean) / std
+    return z
+
+
+def _rolling_periods(rolling_days: int, period_days: float) -> int:
+    if rolling_days <= 0:
+        return 0
+    periods = int(round(rolling_days / max(period_days, 1e-9)))
+    return max(periods, 1)
+
+
+def _calculate_period_years(periods: int, period_days: float) -> float:
+    return (periods * period_days) / 365.25
+
+
+def _compute_rolling_cagr(
+    series: pd.Series, periods: int, period_years: float
+) -> pd.Series:
+    if periods <= 0:
+        return pd.Series(index=series.index, dtype="float64")
+    shifted = series.shift(periods)
+    ratio = series / shifted
+    result = ratio.pow(1.0 / period_years) - 1.0
+    return result
+
+
+def _ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
+    df = df.copy()
+    df["date"] = pd.to_datetime(df["date"], utc=True)
+    return df
+
+
+def compute(
+    df_btc: pd.DataFrame,
+    df_xrp: pd.DataFrame,
+    frequency: str = "M",
+    rebase_date: Optional[pd.Timestamp] = None,
+    z_log: bool = False,
+    rolling_days: Optional[int] = None,
+    include_drawdown: bool = False,
+) -> Tuple[pd.DataFrame, Dict[str, float]]:
+    """Compute aligned metrics for BTC and XRP."""
+
+    btc = _ensure_datetime(df_btc).rename(columns={"price": "btc_usd"})
+    xrp = _ensure_datetime(df_xrp).rename(columns={"price": "xrp_usd"})
+
+    merged = pd.merge(btc, xrp, on="date", how="inner")
+    merged = merged.sort_values("date").reset_index(drop=True)
+
+    merged = merged[(merged["btc_usd"] > 0) & (merged["xrp_usd"] > 0)]
+
+    if merged.empty:
+        raise ValueError("No overlapping positive price data between assets.")
+
+    merged = merged.set_index("date")
+
+    resampled = merged.resample(frequency).last().dropna()
+    resampled = resampled[resampled["btc_usd"] > 0]
+    resampled = resampled[resampled["xrp_usd"] > 0]
+
+    if resampled.empty:
+        raise ValueError("Resampled data is empty after cleaning.")
+
+    if rebase_date is not None:
+        rebase_ts = pd.to_datetime(rebase_date, utc=True)
+        resampled = resampled[resampled.index >= rebase_ts]
+        if resampled.empty:
+            raise ValueError("Rebase date is after available data range.")
+
+    resampled = resampled.sort_index()
+
+    start_date = resampled.index[0]
+    end_date = resampled.index[-1]
+    span_years = (end_date - start_date).days / 365.25
+    span_years = max(span_years, 1e-9)
+
+    resampled["btc_indexed"] = resampled["btc_usd"] / resampled["btc_usd"].iloc[0]
+    resampled["xrp_indexed"] = resampled["xrp_usd"] / resampled["xrp_usd"].iloc[0]
+    resampled["xrp_btc_ratio"] = resampled["xrp_usd"] / resampled["btc_usd"]
+
+    resampled["btc_ret_daily"] = resampled["btc_usd"].pct_change()
+    resampled["xrp_ret_daily"] = resampled["xrp_usd"].pct_change()
+
+    period_days = _estimate_period_days(resampled.index)
+
+    resampled["btc_z"] = compute_z_scores(resampled["btc_usd"], use_log=z_log)
+    resampled["xrp_z"] = compute_z_scores(resampled["xrp_usd"], use_log=z_log)
+
+    resampled["is_month_end"] = resampled.index.is_month_end
+
+    if rolling_days:
+        periods = _rolling_periods(rolling_days, period_days)
+        period_years = _calculate_period_years(periods, period_days)
+        resampled[f"btc_cagr_rolling_{rolling_days}"] = _compute_rolling_cagr(
+            resampled["btc_usd"], periods, period_years
+        )
+        resampled[f"xrp_cagr_rolling_{rolling_days}"] = _compute_rolling_cagr(
+            resampled["xrp_usd"], periods, period_years
+        )
+        resampled[f"ratio_rolling_{rolling_days}"] = (
+            resampled["xrp_btc_ratio"].rolling(window=periods).mean()
+        )
+
+    if include_drawdown:
+        resampled["btc_drawdown"] = compute_drawdown(resampled["btc_usd"])
+        resampled["xrp_drawdown"] = compute_drawdown(resampled["xrp_usd"])
+
+    summary = Summary(
+        start_date=start_date.to_pydatetime(),
+        end_date=end_date.to_pydatetime(),
+        span_years=(end_date - start_date).days / 365.25,
+        btc_start_price=float(resampled["btc_usd"].iloc[0]),
+        btc_end_price=float(resampled["btc_usd"].iloc[-1]),
+        xrp_start_price=float(resampled["xrp_usd"].iloc[0]),
+        xrp_end_price=float(resampled["xrp_usd"].iloc[-1]),
+        btc_cagr=calculate_cagr(
+            float(resampled["btc_usd"].iloc[0]),
+            float(resampled["btc_usd"].iloc[-1]),
+            span_years,
+        ),
+        xrp_cagr=calculate_cagr(
+            float(resampled["xrp_usd"].iloc[0]),
+            float(resampled["xrp_usd"].iloc[-1]),
+            span_years,
+        ),
+        ratio_start=float(resampled["xrp_btc_ratio"].iloc[0]),
+        ratio_end=float(resampled["xrp_btc_ratio"].iloc[-1]),
+    )
+
+    result = resampled.reset_index().rename(columns={"date": "date"})
+    result["date"] = result["date"].dt.date
+
+    return result, summary.to_dict()
+
+
+__all__ = [
+    "compute",
+    "calculate_cagr",
+    "compute_drawdown",
+    "compute_z_scores",
+]
 
EOF
)
