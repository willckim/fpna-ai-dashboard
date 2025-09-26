# python/make_visuals.py
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "data"

def save_line(df, x, ys, title, fname, xlabel="Month", ylabel="Value"):
    plt.figure()
    for y in ys:
        if y in df.columns:
            plt.plot(df[x], df[y], label=y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=160)
    plt.close()

def save_bar(df, x, y, title, fname, xlabel=None, ylabel=None):
    plt.figure()
    plt.bar(df[x], df[y])
    plt.title(title)
    plt.xlabel(xlabel or x)
    plt.ylabel(ylabel or y)
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=160)
    plt.close()

def main():
    # 1) Trend: Actual vs Budget
    trend = pd.read_csv(DATA / "monthly_trend.csv")
    save_line(
        trend,
        x="Month",
        ys=["Actual_Revenue", "Budget_Forecast", "Gross_Profit"],
        title="Revenue vs Budget (Trend)",
        fname="viz_trend.png",
        ylabel="USD"
    )

    # 2) Variance by Department (bar, sorted by Variance_Pct)
    dept = pd.read_csv(DATA / "variance_summary.csv").sort_values("Variance_Pct", ascending=False)
    save_bar(
        dept,
        x="Department",
        y="Variance_Pct",
        title="Variance % by Department",
        fname="viz_dept_variance.png",
        ylabel="Variance %"
    )

    # 3) Forecast by Department (line)
    fby = pd.read_csv(DATA / "forecast_by_department.csv")
    # Pivot to lines per department
    pivot = fby.pivot(index="Month", columns="Department", values="Forecast").reset_index()
    save_line(
        pivot,
        x="Month",
        ys=[c for c in pivot.columns if c != "Month"],
        title="Forecast by Department (Next 6 Months)",
        fname="viz_forecast_dept.png",
        ylabel="USD"
    )

    print("✅ Saved charts:")
    print("  - data/viz_trend.png")
    print("  - data/viz_dept_variance.png")
    print("  - data/viz_forecast_dept.png")

if __name__ == "__main__":
    main()
