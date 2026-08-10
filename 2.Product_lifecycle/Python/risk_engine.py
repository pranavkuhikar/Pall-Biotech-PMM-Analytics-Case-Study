import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

DB_USER="PRANAV"
DB_PASSWORD="pranav123456"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="pall_pmm_case_study"

engine=create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

BASE_DIR=Path(__file__).resolve().parent.parent
RISK_DIR=BASE_DIR/"Outputs"/"Risk"
RISK_DIR.mkdir(parents=True,exist_ok=True)

df=pd.read_sql("SELECT * FROM initiatives_scored",engine)

# Composite risk score
df["risk_score"]=(
    (1-df["aos_health"])*50+
    (df["backlog_days"]/df["backlog_days"].max())*20+
    ((100-df["actual_otd_pct"])/100)*15+
    ((1-df["revenue_attainment"]))*15
).round(2)

watchlist=df.sort_values("risk_score",ascending=False).head(25)
watchlist.to_csv(RISK_DIR/"executive_watchlist.csv",index=False)

high=df[df["risk_score"]>=df["risk_score"].quantile(.90)]\
    .sort_values("risk_score",ascending=False)
high.to_csv(RISK_DIR/"high_risk_initiatives.csv",index=False)

regional=df.groupby("region").agg(
    avg_aos=("aos_health","mean"),
    avg_backlog=("backlog_days","mean"),
    avg_otd=("actual_otd_pct","mean"),
    revenue=("actual_revenue","sum"),
    initiatives=("initiative_id","nunique")
).reset_index()
regional["risk_score"]=(
    (1-regional.avg_aos)*60+
    (regional.avg_backlog/regional.avg_backlog.max())*40
).round(2)
regional=regional.sort_values("risk_score",ascending=False)
regional.to_csv(RISK_DIR/"regional_risk.csv",index=False)

bu=df.groupby("business_unit").agg(
    avg_aos=("aos_health","mean"),
    avg_backlog=("backlog_days","mean"),
    avg_otd=("actual_otd_pct","mean"),
    revenue=("actual_revenue","sum"),
    initiatives=("initiative_id","nunique")
).reset_index()
bu["risk_score"]=(
    (1-bu.avg_aos)*60+
    (bu.avg_backlog/bu.avg_backlog.max())*40
).round(2)
bu=bu.sort_values("risk_score",ascending=False)
bu.to_csv(RISK_DIR/"business_unit_risk.csv",index=False)

owner=df.groupby("owner").agg(
    initiatives=("initiative_id","nunique"),
    avg_aos=("aos_health","mean"),
    avg_otd=("actual_otd_pct","mean"),
    revenue=("actual_revenue","sum")
).reset_index().sort_values("avg_aos",ascending=False)
owner.to_csv(RISK_DIR/"owner_performance.csv",index=False)

summary=f"""
PLCM PORTFOLIO RISK SUMMARY
===========================

Total Initiatives : {df['initiative_id'].nunique()}
Observations      : {len(df)}
Average AOS       : {df['aos_health'].mean():.3f}

Highest Risk Region
-------------------
{regional.iloc[0]['region']}

Highest Risk Business Unit
--------------------------
{bu.iloc[0]['business_unit']}

Highest Risk Initiative
-----------------------
{watchlist.iloc[0]['initiative_name']}

Green : {(df['status']=='Green').sum()}
Amber : {(df['status']=='Amber').sum()}
Red   : {(df['status']=='Red').sum()}

Recommendations
---------------
1. Review top 25 initiatives in executive_watchlist.csv
2. Prioritize regions with highest backlog.
3. Improve OTD for low-performing initiatives.
4. Review owner performance for coaching/resource allocation.
"""
(RISK_DIR/"risk_summary.txt").write_text(summary,encoding="utf-8")

print("Risk outputs generated:")
for f in RISK_DIR.iterdir():
    print(" -",f)