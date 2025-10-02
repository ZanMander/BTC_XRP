 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/tests/test_alignment.py
index 0000000000000000000000000000000000000000..de8bb680a244b09f5a38d2e1578ad96fcad72c6a 100644
--- a//dev/null
+++ b/tests/test_alignment.py
@@ -0,0 +1,38 @@
+import pandas as pd
+
+from core.compute import compute
+
+
+def test_alignment_overlapping_dates():
+    btc_dates = pd.date_range("2020-01-01", periods=6, freq="D")
+    xrp_dates = pd.date_range("2020-01-03", periods=6, freq="D")
+
+    btc_prices = [100, 105, 110, 115, 120, 125]
+    xrp_prices = [0.2, 0.21, 0.22, 0.23, 0.24, 0.25]
+
+    df_btc = pd.DataFrame({"date": btc_dates, "price": btc_prices})
+    df_xrp = pd.DataFrame({"date": xrp_dates, "price": xrp_prices})
+
+    result, summary = compute(df_btc, df_xrp, frequency="D")
+
+    assert result["date"].iloc[0].isoformat() == "2020-01-03"
+    assert result["date"].iloc[-1].isoformat() == "2020-01-08"
+
+    required_columns = {
+        "btc_usd",
+        "xrp_usd",
+        "btc_indexed",
+        "xrp_indexed",
+        "xrp_btc_ratio",
+        "btc_ret_daily",
+        "xrp_ret_daily",
+        "btc_z",
+        "xrp_z",
+        "is_month_end",
+    }
+    assert required_columns.issubset(result.columns)
+    assert not result["btc_usd"].isna().any()
+    assert not result["xrp_usd"].isna().any()
+
+    assert summary["start_date"].strftime("%Y-%m-%d") == "2020-01-03"
+    assert summary["end_date"].strftime("%Y-%m-%d") == "2020-01-08"
 
EOF
)
