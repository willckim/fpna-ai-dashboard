# python/forecast.py
import math
from pathlib import Path
import pandas as pd

# Try to import statsmodels for Holt-Winters forecasting
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    HAS_SM = True
except Exception:
    HAS_SM = False

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
INPUT = DATA_DIR / "financials.csv"      # <-- directly use your dataset with Department
OUTPUT = DATA_DIR / "forecast_by_department.csv"

HORIZON = 6   # forecast 6 months
ROLLING_WINDOW = 3  # fallback rolling mean

def forecast_series(series: pd.Series) -> pd.DataFrame:
    """
    Forecast one series for HORIZON months.
    If statsmodels unavailable, fallback to rolling mean.
    Returns DataFrame with Month, Forecast, Lower, Upper
    """
    s = series.dropna().astype(float)
    if s.empty:
        return pd.DataFrame(columns=["Month", "Forecast", "Lower", "Upper"])

    # Convert to datetime index
    s.index = pd.to_datetime(s.index)
    s = s.asfreq("MS")  # Monthly start

    # Fallback path if no statsmodels or not enough history
    if (not HAS_SM) or (len(s) < max(ROLLING_WINDOW + 1, 4)):
        avg = s.rolling(ROLLING_WINDOW).mean().iloc[-1]
        if pd.isna(avg):
            avg = s.iloc[-1]
        residual_std = s.rolling(ROLLING_WINDOW).std().iloc[-1]
        if pd.isna(residual_std):
            residual_std = s.std() if len(s) > 1 else 0.0

        last_month = s.index[-1]
        future_idx = pd.date_range(last_month + pd.offsets.MonthBegin(1), periods=HORIZON, freq="MS")

        z = 1.96  # 95% CI
        return pd.DataFrame({
            "Month": future_idx.strftime("%Y-%m"),
            "Forecast": [float(avg)] * HORIZON,
            "Lower": [float(avg - z * residual_std)] * HORIZON,
            "Upper": [float(avg + z * residual_std)] * HORIZON
        })

    # Statsmodels Holt-Winters
    try:
        model = ExponentialSmoothing(
            s,
            trend="add",
            seasonal="add",
            seasonal_periods=12 if len(s) >= 24 else None,
            initialization_method="estimated",
            freq="MS",
        ).fit(optimized=True)

        forecast_vals = model.forecast(HORIZON)
        resid = model.resid
        resid_std = resid.std(ddof=1) if len(resid) > 1 else 0.0
        z = 1.96
        lower = forecast_vals - z * resid_std
        upper = forecast_vals + z * resid_std

        return pd.DataFrame({
            "Month": forecast_vals.index.strftime("%Y-%m"),
            "Forecast": forecast_vals.values.astype(float),
            "Lower": lower.values.astype(float),
            "Upper": upper.values.astype(float),
        })
    except Exception:
        # fallback again
        avg = s.iloc[-ROLLING_WINDOW:].mean()
        residual_std = s.std() if len(s) > 1 else 0.0
        last_month = s.index[-1]
        future_idx = pd.date_range(last_month + pd.offsets.MonthBegin(1), periods=HORIZON, freq="MS")
        z = 1.96
        return pd.DataFrame({
            "Month": future_idx.strftime("%Y-%m"),
            "Forecast": [float(avg)] * HORIZON,
            "Lower": [float(avg - z * residual_std)] * HORIZON,
            "Upper": [float(avg + z * residual_std)] * HORIZON
        })

def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing {INPUT}")

    df = pd.read_csv(INPUT)
    required = {"Month", "Department", "Revenue"}
    if missing := (required - set(df.columns)):
        raise ValueError(f"Missing columns in {INPUT}: {missing}")

    # Convert Month to datetime
    df["MonthKey"] = pd.to_datetime(df["Month"] + "-01")

    forecasts = []

    for dept, sub in df.groupby("Department"):
        series = sub.set_index("MonthKey")["Revenue"].sort_index()
        f = forecast_series(series)
        f["Department"] = dept
        forecasts.append(f)

    out = pd.concat(forecasts, ignore_index=True)
    out = out[["Month", "Department", "Forecast", "Lower", "Upper"]]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print("✅ Wrote department-level forecast →", OUTPUT)
    print(out.head(12).to_string(index=False))

if __name__ == "__main__":
    main()
