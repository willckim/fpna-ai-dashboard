# FP&A AI Dashboard

An **AI-powered Financial Planning & Analysis (FP&A) project** showcasing variance analysis, forecasting, and automated executive summaries.  
Built with **Python (pandas, statsmodels, OpenAI/Azure OpenAI)** and visualized in **Power BI**.

---

## 🚀 Features

- **Variance Analysis**  
  - SQL/Pandas pipeline calculates Actual vs. Budget, Variance %, and Gross Margin.  
  - Department-level and monthly trend views.  

- **Forecasting**  
  - Department-level forecasting using statistical models.  
  - Produces a 3–6 month forward outlook with upper/lower confidence bounds.  

- **AI Executive Summary**  
  - Auto-generates 4–6 sentence FP&A-style narratives.  
  - Runs locally with fallback (rule-based summary).  
  - If keys are provided, integrates with **Azure OpenAI** or **OpenAI API** for polished language.  

- **Interactive BI**  
  - Data outputs (`.csv`) imported into **Power BI/Tableau** for dashboards.  
  - Supports variance heatmaps, monthly trend lines, and department forecasting visuals.

---

## 📂 Project Structure

fpna-ai-dashboard/
├── data/
│ ├── financials.csv # Raw dataset (input)
│ ├── variance_summary.csv # Dept rollup
│ ├── monthly_trend.csv # Revenue/profit trend
│ ├── department_variance.csv # Dept-level variance table
│ ├── latest_kpis.csv # Most recent KPIs
│ ├── forecast_by_department.csv # Forecasted revenues by dept
│ └── exec_summary.md # AI-generated executive summary
├── python/
│ ├── variance_analysis.py # Variance + KPI pipeline
│ ├── forecast.py # Forecasting by department
│ └── ai_summary.py # AI/LLM executive summary
└── README.md