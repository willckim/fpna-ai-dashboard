# python/ai_summary.py
import os
import math
import pandas as pd
from pathlib import Path

# --- Optional: load .env if present ---
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
kpis_path = DATA_DIR / "latest_kpis.csv"
dept_var_path = DATA_DIR / "variance_summary.csv"
fcst_dept_path = DATA_DIR / "forecast_by_department.csv"  # optional

# ---------- Load data ----------
kpis = pd.read_csv(kpis_path)
dept_var = pd.read_csv(dept_var_path).sort_values("Variance_Pct", ascending=True)

month = str(kpis["Month"].iloc[0])
actual = float(kpis["Actual_Total"].iloc[0])
budget = float(kpis["Budget_Total"].iloc[0])
variance = float(kpis["Variance_Total"].iloc[0])
variance_pct = float(kpis["Variance_Pct"].iloc[0])
gm_pct = float(kpis["Gross_Margin_Pct"].iloc[0])

top_over = dept_var.sort_values("Variance_Pct", ascending=False).head(2)[["Department", "Variance_Pct"]]
top_under = dept_var.sort_values("Variance_Pct", ascending=True).head(2)[["Department", "Variance_Pct"]]

# ---------- Optional forecast load ----------
fcst_summary_line = None
fcst_details_line = None
if fcst_dept_path.exists():
    fc = pd.read_csv(fcst_dept_path)  # Month, Department, Forecast, Lower, Upper
    fc["Month"] = fc["Month"].astype(str)

    # Build next3 WITHOUT groupby.apply to avoid FutureWarning and keep Department column
    parts = []
    for dept, d in fc.groupby("Department"):
        d_sorted = d.sort_values("Month").head(3)
        parts.append(d_sorted)
    next3 = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=fc.columns)

    # Average of first 3 forecast months per department
    if not next3.empty:
        by_dept = (
            next3.groupby("Department", as_index=False)
                 .agg(Forecast_Avg=("Forecast", "mean"))
        )
        overall_avg = by_dept["Forecast_Avg"].mean()
        if pd.notna(overall_avg) and overall_avg != 0:
            by_dept["Delta_vs_Pool_%"] = (by_dept["Forecast_Avg"] / overall_avg - 1.0) * 100
        else:
            by_dept["Delta_vs_Pool_%"] = 0.0

        movers_up = by_dept.sort_values("Delta_vs_Pool_%", ascending=False).head(1)
        movers_down = by_dept.sort_values("Delta_vs_Pool_%", ascending=True).head(1)

        def _fmt_pair(df):
            if df.empty:
                return None
            r = df.iloc[0]
            return f"{r['Department']} ({r['Delta_vs_Pool_%']:+.1f}%)"

        up_text = _fmt_pair(movers_up)
        down_text = _fmt_pair(movers_down)

        # Total next-3-months forecast (avg of monthly totals)
        total_next3 = next3.groupby("Month")["Forecast"].sum().mean()
        if pd.notna(total_next3):
            fcst_summary_line = f"• **Forward look (next 3 months):** average projected revenue ≈ ${total_next3:,.0f}."
        if up_text or down_text:
            bits = []
            if up_text: bits.append(f"Upside leader: {up_text}")
            if down_text: bits.append(f"Downside risk: {down_text}")
            fcst_details_line = "• " + " | ".join(bits)

def fmt_pct(x): return f"{x:+.1f}%"
def money(x): return f"${x:,.0f}"

# ---------- Rule-based fallback ----------
fallback_lines = [
    f"**Executive Summary – {month}**",
    f"• Revenue was {money(actual)} vs budget {money(budget)} ({fmt_pct(variance_pct)} variance). "
    f"Gross margin {gm_pct:.1f}%.",
    ("• Overall performance was **above budget**; monitor sustainability into next month."
     if variance_pct >= 0 else
     "• Overall performance was **below budget**; investigate drivers and corrective actions."),
]
if not top_over.empty:
    over_str = ", ".join(f"{r.Department} ({fmt_pct(r.Variance_Pct)})" for r in top_over.itertuples(index=False))
    fallback_lines.append(f"• Biggest **unfavorable variances**: {over_str}.")
if not top_under.empty:
    under_str = ", ".join(f"{r.Department} ({fmt_pct(r.Variance_Pct)})" for r in top_under.itertuples(index=False))
    fallback_lines.append(f"• Biggest **favorable variances**: {under_str}.")
if fcst_summary_line: fallback_lines.append(fcst_summary_line)
if fcst_details_line: fallback_lines.append(fcst_details_line)
fallback_lines.append("• Next steps: review cost drivers in unfavorable areas, validate forecast assumptions, "
                      "and refresh the rolling 3-month outlook.")
fallback_md = "\n".join(fallback_lines)

# ---------- Provider selection ----------
provider = "fallback"
text = fallback_md

azure_key = os.getenv("AZURE_OPENAI_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-07-18")
openai_key = os.getenv("OPENAI_API_KEY")

# Build prompt (include forward outlook if available)
prompt = f"""
You are an FP&A analyst. Write a crisp executive summary (4–6 sentences) for {month}.
Actuals:
- Actual: {actual:.2f}
- Budget: {budget:.2f}
- Variance: {variance:.2f} ({variance_pct:.2f}%)
- Gross Margin %: {gm_pct:.2f}
Unfavorable depts: {top_over.to_dict(orient="records")}
Favorable depts: {top_under.to_dict(orient="records")}
Forward look (if provided):
- {fcst_summary_line or "n/a"}
- {fcst_details_line or "n/a"}
Be specific, neutral, and include 1–2 actionable next steps. Return markdown with a bold title.
""".strip()

try:
    if azure_key and azure_endpoint and azure_deployment:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=azure_key,
            azure_endpoint=azure_endpoint,
            api_version=azure_api_version
        )
        resp = client.chat.completions.create(
            model=azure_deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        provider = "azure"
    elif openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        provider = "openai"
except Exception as e:
    text = fallback_md + f"\n\n> (LLM unavailable, using fallback: {e})"
    provider = "fallback-error"

# ---------- Write output ----------
out_path = DATA_DIR / "exec_summary.md"
out_path.write_text(text, encoding="utf-8")
print(f"✅ Wrote executive summary → {out_path}")
print(f"🔎 Provider used: {provider}")
