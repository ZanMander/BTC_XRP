 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/core/data_source.py
index 0000000000000000000000000000000000000000..1fea99a9027a767f63f3140bb73e058687e99fab 100644
--- a//dev/null
+++ b/core/data_source.py
@@ -0,0 +1,120 @@
+"""Data fetching utilities for CoinGecko market data."""
+from __future__ import annotations
+
+import json
+import time
+from dataclasses import dataclass
+from datetime import datetime, timedelta, timezone
+from pathlib import Path
+from typing import Any, Dict, Optional
+
+import pandas as pd
+import requests
+
+
+CACHE_DIR = Path("data")
+CACHE_DIR.mkdir(parents=True, exist_ok=True)
+
+API_URL_TEMPLATE = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
+DEFAULT_SLEEP_SECONDS = 1.1
+
+
+@dataclass
+class MarketChartResponse:
+    """Container for CoinGecko market chart data."""
+
+    prices: list[tuple[int, float]]
+
+    @classmethod
+    def from_json(cls, payload: Dict[str, Any]) -> "MarketChartResponse":
+        if "prices" not in payload:
+            raise ValueError("Unexpected payload structure: missing 'prices'")
+        prices: list[list[float]] = payload["prices"]
+        normalized = [(int(ts), float(price)) for ts, price in prices]
+        return cls(prices=normalized)
+
+
+def _cache_file_for_coin(coin_id: str) -> Path:
+    return CACHE_DIR / f"cache_{coin_id}.json"
+
+
+def _is_cache_valid(path: Path, ttl_hours: int) -> bool:
+    if not path.exists():
+        return False
+    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
+    return datetime.now(tz=timezone.utc) - modified < timedelta(hours=ttl_hours)
+
+
+def _load_from_cache(path: Path) -> Optional[Dict[str, Any]]:
+    try:
+        with path.open("r", encoding="utf-8") as f:
+            return json.load(f)
+    except json.JSONDecodeError:
+        return None
+
+
+def _write_to_cache(path: Path, payload: Dict[str, Any]) -> None:
+    with path.open("w", encoding="utf-8") as f:
+        json.dump(payload, f)
+
+
+def fetch_market_chart(
+    coin_id: str,
+    vs_currency: str = "usd",
+    days: str = "max",
+    cache_ttl_hours: int = 24,
+    session: Optional[requests.Session] = None,
+) -> pd.DataFrame:
+    """Fetch market chart data for a coin, with local caching.
+
+    Parameters
+    ----------
+    coin_id: str
+        CoinGecko identifier for the asset (e.g., "bitcoin").
+    vs_currency: str
+        Quote currency for prices (default: "usd").
+    days: str
+        Range of days to request (default: "max").
+    cache_ttl_hours: int
+        Cache time-to-live in hours.
+    session: Optional[requests.Session]
+        Optional requests session for connection pooling.
+
+    Returns
+    -------
+    pd.DataFrame
+        DataFrame with columns ``date`` (datetime normalized to UTC midnight)
+        and ``price`` (float), representing the last observed price per day.
+    """
+
+    cache_path = _cache_file_for_coin(coin_id)
+    payload: Optional[Dict[str, Any]] = None
+    if _is_cache_valid(cache_path, cache_ttl_hours):
+        payload = _load_from_cache(cache_path)
+
+    if payload is None:
+        params = {"vs_currency": vs_currency, "days": days}
+        url = API_URL_TEMPLATE.format(coin_id=coin_id)
+        http = session or requests.Session()
+        response = http.get(url, params=params, timeout=30)
+        if response.status_code != 200:
+            raise RuntimeError(
+                f"Failed to fetch data for {coin_id}: {response.status_code} {response.text}"
+            )
+        payload = response.json()
+        _write_to_cache(cache_path, payload)
+        time.sleep(DEFAULT_SLEEP_SECONDS)
+
+    chart = MarketChartResponse.from_json(payload)
+    if not chart.prices:
+        raise ValueError(f"No price data returned for {coin_id}")
+
+    df = pd.DataFrame(chart.prices, columns=["timestamp", "price"])
+    df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.normalize()
+    daily_df = (
+        df.groupby("date", as_index=False)["price"].last().sort_values("date").reset_index(drop=True)
+    )
+    return daily_df[["date", "price"]]
+
+
+__all__ = ["fetch_market_chart"]
 
EOF
)
