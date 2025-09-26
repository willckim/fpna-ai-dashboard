# python/variance_analysis.py
import pandas as pd
from pathlib import Path

# ---------- Paths ----------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INPUT = DATA_DIR / "financials.csv"

# ---------- Load ----------
df = pd.read_csv(INPUT)

# Validate schema
expected = {"Month", "Department", "Revenue", "Expense", "Forecast_Revenue"}
missing = expected - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in financials.csv: {missing}")

# ---------- Derivations ----------
df["Gross_Profit"] = df["Revenue"] - df["Expense"]
df["Gross_Margin_Pct"] = (
    (df["Gross_Profit"] / df["Revenue"]).where(df["Revenue"] != 0)
).round(4) * 100

df["Variance_vs_Forecast"] = df["Revenue"] - df["Forecast_Revenue"]
df["Variance_Pct"] = (
    (df["Variance_vs_Forecast"] / df["Forecast_Revenue"]).where(df["Forecast_Revenue"] != 0)
).round(4) * 100

# Normalize Month to YYYY-MM and add sortable key
df["Month"] = df["Month"].astype(str).str[:7]
df["MonthKey"] = pd.to_datetime(df["Month"] + "-01")

# ---------- 1) Department rollup ----------
summary = (
    df.groupby("Department", as_index=False)
    .agg(
        Actual_Total=("Revenue", "sum"),
        Budget_Total=("Forecast_Revenue", "sum"),
        Variance_Total=("Variance_vs_Forecast", "sum"),
        Avg_Gross_Margin_Pct=("Gross_Margin_Pct", "mean"),
    )
    .sort_values("Actual_Total", ascending=False)
)
summary["Variance_Pct"] = (
    (summary["Variance_Total"] / summary["Budget_Total"]).where(summary["Budget_Total"] != 0)
).round(4) * 100

# ---------- 2) Monthly trend ----------
trend = (
    df.groupby(["Month", "MonthKey"], as_index=False)
    .agg(
        Actual_Revenue=("Revenue", "sum"),
        Budget_Forecast=("Forecast_Revenue", "sum"),
        Gross_Profit=("Gross_Profit", "sum"),
    )
    .sort_values("MonthKey")
)

# Optional YoY growth (valid after 12 months)
trend["YoY_Actual_Revenue"] = (
    trend.set_index("MonthKey")["Actual_Revenue"].pct_change(12).reset_index(drop=True) * 100
).round(2)

# ---------- 3) Department variance by month ----------
dept_var = df[
    [
        "Month",
        "MonthKey",
        "Department",
        "Revenue",
        "Forecast_Revenue",
        "Variance_vs_Forecast",
        "Variance_Pct",
        "Gross_Margin_Pct",
    ]
].sort_values(["MonthKey", "Department"])

# ---------- 4) Latest month KPIs (single-row) ----------
latest_key = df["MonthKey"].max()

# Aggregate to a Series, then to one-row DataFrame
latest_series = df[df["MonthKey"] == latest_key].agg(
    {
        "Revenue": "sum",
        "Forecast_Revenue": "sum",
        "Variance_vs_Forecast": "sum",
        "Gross_Profit": "sum",
    }
)
latest = latest_series.to_frame().T.rename(
    columns={
        "Revenue": "Actual_Total",
        "Forecast_Revenue": "Budget_Total",
        "Variance_vs_Forecast": "Variance_Total",
    }
)

latest["Variance_Pct"] = (
    (latest["Variance_Total"] / latest["Budget_Total"]).where(latest["Budget_Total"] != 0) * 100
)
latest["Gross_Margin_Pct"] = (
    (latest["Gross_Profit"] / latest["Actual_Total"]).where(latest["Actual_Total"] != 0) * 100
)
latest["Month"] = df.loc[df["MonthKey"] == latest_key, "Month"].iloc[0]
latest = latest[
    ["Month", "Actual_Total", "Budget_Total", "Variance_Total", "Variance_Pct", "Gross_Margin_Pct"]
].round(2)

# ---------- Save outputs ----------
OUTPUTS = {
    "variance_summary.csv": summary.round(2),
    "monthly_trend.csv": trend.round(2).drop(columns=["MonthKey"]),
    "department_variance.csv": dept_var.round(2).drop(columns=["MonthKey"]),
    "latest_kpis.csv": latest.round(2),
}

DATA_DIR.mkdir(parents=True, exist_ok=True)
for name, frame in OUTPUTS.items():
    frame.to_csv(DATA_DIR / name, index=False)

print("✅ Generated:")
for name in OUTPUTS:
    print(f"  - data/{name}")
