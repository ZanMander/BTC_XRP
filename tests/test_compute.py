 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/tests/test_compute.py
index 0000000000000000000000000000000000000000..a8ce48fdced4cccc43e6bb5cd4bee0402c7dce8a 100644
--- a//dev/null
+++ b/tests/test_compute.py
@@ -0,0 +1,39 @@
+import math
+
+import numpy as np
+import pandas as pd
+
+from core.compute import calculate_cagr, compute, compute_z_scores
+
+
+def test_calculate_cagr_basic():
+    result = calculate_cagr(100.0, 121.0, 2.0)
+    assert math.isclose(result, 0.1, rel_tol=1e-9)
+
+
+def test_compute_ratio_and_cagr():
+    dates = pd.date_range("2020-01-01", periods=5, freq="D")
+    btc_prices = [100, 110, 120, 130, 140]
+    xrp_prices = [1, 1.1, 1.2, 1.3, 1.4]
+
+    df_btc = pd.DataFrame({"date": dates, "price": btc_prices})
+    df_xrp = pd.DataFrame({"date": dates, "price": xrp_prices})
+
+    result, summary = compute(df_btc, df_xrp, frequency="D")
+
+    ratio = result["xrp_usd"] / result["btc_usd"]
+    assert np.allclose(result["xrp_btc_ratio"], ratio)
+
+    years = (dates[-1] - dates[0]).days / 365.25
+    expected_cagr = calculate_cagr(100.0, 140.0, years)
+    assert math.isclose(summary["btc_cagr"], expected_cagr, rel_tol=1e-9)
+
+
+def test_compute_z_scores_normalization():
+    dates = pd.date_range("2021-01-01", periods=10, freq="D")
+    series = pd.Series(range(1, 11), index=dates)
+
+    z_scores = compute_z_scores(series)
+
+    assert abs(float(z_scores.mean())) < 1e-12
+    assert math.isclose(float(z_scores.std(ddof=0)), 1.0, rel_tol=1e-9)
 
EOF
)
