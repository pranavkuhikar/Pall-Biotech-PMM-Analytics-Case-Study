
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"

INPUT_FILE = DATA_DIR / "initiatives.csv"
OUTPUT_FILE = DATA_DIR / "initiatives_scored.csv"
SUMMARY_FILE = DATA_DIR / "plcm_summary.csv"
RANKING_FILE = DATA_DIR / "initiative_ranking.csv"

print("="*80)
print("AOS HEALTH SCORING")
print("="*80)

df = pd.read_csv(INPUT_FILE)

# ------------------------------------------------------------------
# Core KPI Calculations
# ------------------------------------------------------------------
df["revenue_attainment"] = (
    df["actual_revenue"] / df["planned_revenue"]
).clip(0,1.25)

df["otd_attainment"] = (
    df["actual_otd_pct"] / df["planned_otd_pct"]
).clip(0,1.10)

df["backlog_score"] = (
    1 - (df["backlog_days"]/90)
).clip(0,1)

df["adoption_score"] = (
    df["customer_adoption_pct"]/100
).clip(0,1)

df["margin_score"] = (
    df["gross_margin_pct"]/50
).clip(0,1)

budget_gap = abs(df["budget_utilization_pct"]-100)
df["budget_score"] = (
    1-budget_gap/50
).clip(0,1)

# ------------------------------------------------------------------
# AOS Score
# ------------------------------------------------------------------
weights = {
    "revenue_attainment":0.35,
    "otd_attainment":0.20,
    "backlog_score":0.15,
    "adoption_score":0.10,
    "margin_score":0.10,
    "budget_score":0.10
}

df["aos_health"] = (
      df["revenue_attainment"]*weights["revenue_attainment"]
    + df["otd_attainment"]*weights["otd_attainment"]
    + df["backlog_score"]*weights["backlog_score"]
    + df["adoption_score"]*weights["adoption_score"]
    + df["margin_score"]*weights["margin_score"]
    + df["budget_score"]*weights["budget_score"]
)

df["execution_score"] = (
    df["otd_attainment"]*0.5 +
    df["backlog_score"]*0.5
)

df["revenue_variance_pct"] = (
    (df["actual_revenue"]-df["planned_revenue"])
    /df["planned_revenue"]*100
)

df["otd_variance_pct"] = (
    df["actual_otd_pct"]-df["planned_otd_pct"]
)

def status(score):
    if score >= 0.90:
        return "Green"
    elif score >= 0.75:
        return "Amber"
    return "Red"

df["status"] = df["aos_health"].apply(status)

def risk(score):
    if score >= 0.90:
        return "Low"
    elif score >= 0.75:
        return "Medium"
    return "High"

df["risk_category"] = df["aos_health"].apply(risk)

df["priority_rank"] = (
    df.groupby("quarter")["aos_health"]
      .rank(method="dense", ascending=False)
      .astype(int)
)

for c in [
    "revenue_attainment","otd_attainment","backlog_score",
    "adoption_score","margin_score","budget_score",
    "execution_score","aos_health"
]:
    df[c]=df[c].round(3)

df.to_csv(OUTPUT_FILE,index=False)

summary = (
    df.groupby(["business_unit","region"])
      .agg(
        initiatives=("initiative_id","nunique"),
        observations=("initiative_id","count"),
        avg_aos=("aos_health","mean"),
        avg_revenue_attainment=("revenue_attainment","mean"),
        avg_otd=("actual_otd_pct","mean"),
        avg_backlog=("backlog_days","mean"),
        total_revenue=("actual_revenue","sum")
      )
      .reset_index()
)

summary["avg_aos"]=summary["avg_aos"].round(3)
summary.to_csv(SUMMARY_FILE,index=False)

ranking = (
    df.groupby(["initiative_id","initiative_name","business_unit"])
      .agg(
        avg_aos=("aos_health","mean"),
        total_revenue=("actual_revenue","sum"),
        avg_otd=("actual_otd_pct","mean"),
        avg_backlog=("backlog_days","mean")
      )
      .reset_index()
      .sort_values("avg_aos",ascending=False)
)

ranking["rank"]=range(1,len(ranking)+1)
ranking.to_csv(RANKING_FILE,index=False)

print(f"Loaded rows: {len(df):,}")
print(f"Unique initiatives: {df['initiative_id'].nunique()}")
print(f"Average AOS: {df['aos_health'].mean():.3f}")
print(f"Green: {(df['status']=='Green').sum()}")
print(f"Amber: {(df['status']=='Amber').sum()}")
print(f"Red: {(df['status']=='Red').sum()}")

print("\nSaved:")
print(OUTPUT_FILE)
print(SUMMARY_FILE)
print(RANKING_FILE)
