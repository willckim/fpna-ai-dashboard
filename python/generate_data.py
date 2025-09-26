import pandas as pd
import numpy as np
import os

# Ensure data folder exists
os.makedirs("../data", exist_ok=True)

# Months
months = pd.date_range("2023-01-01", periods=24, freq="M")  # 2 years

# Departments
departments = ["Sales", "Marketing", "Operations", "R&D"]

rows = []
for dept in departments:
    base_revenue = np.random.randint(50000, 150000)
    base_expense = np.random.randint(30000, 80000)

    for month in months:
        revenue = base_revenue + np.random.randint(-10000, 15000)
        expense = base_expense + np.random.randint(-5000, 10000)
        forecast = revenue * (1 + np.random.uniform(-0.05, 0.1))  # ±5–10%

        rows.append({
            "Month": month.strftime("%Y-%m"),
            "Department": dept,
            "Revenue": revenue,
            "Expense": expense,
            "Forecast_Revenue": round(forecast, 2)
        })

# Save to CSV inside /data
output_path = os.path.join("..", "data", "financials.csv")
pd.DataFrame(rows).to_csv(output_path, index=False)

print(f"✅ financials.csv generated at {output_path}")
