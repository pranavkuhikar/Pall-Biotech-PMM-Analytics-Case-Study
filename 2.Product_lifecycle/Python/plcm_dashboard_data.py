import pandas as pd
from sqlalchemy import create_engine

from pathlib import Path

# ==========================
# DATABASE CONFIG
# ==========================
DB_USER="PRANAV"
DB_PASSWORD="pranav123456"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="pall_pmm_case_study"

engine=create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

BASE_DIR=Path(__file__).resolve().parent.parent
OUTPUT_DIR=BASE_DIR/"Outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

print("="*80)
print("PLCM DASHBOARD DATA GENERATOR")
print("="*80)

# ---------------- Executive KPIs ----------------
executive=pd.read_sql("""
SELECT
COUNT(DISTINCT initiative_id) total_initiatives,
COUNT(*) observations,
ROUND(AVG(aos_health)::numeric,3) avg_aos,
ROUND(AVG(actual_otd_pct)::numeric,2) avg_otd,
ROUND(AVG(backlog_days)::numeric,2) avg_backlog,
ROUND(SUM(actual_revenue)::numeric,2) total_revenue,
SUM(CASE WHEN status='Green' THEN 1 ELSE 0 END) green,
SUM(CASE WHEN status='Amber' THEN 1 ELSE 0 END) amber,
SUM(CASE WHEN status='Red' THEN 1 ELSE 0 END) red
FROM initiatives_scored;
""",engine)

# ---------------- Business Unit ----------------
business=pd.read_sql("""
SELECT *
FROM vw_aos_summary
ORDER BY avg_aos DESC;
""",engine)

# ---------------- Region ----------------
region=pd.read_sql("""
SELECT
region,
COUNT(DISTINCT initiative_id) initiatives,
ROUND(AVG(aos_health)::numeric,3) avg_aos,
ROUND(AVG(actual_otd_pct)::numeric,2) avg_otd,
ROUND(AVG(backlog_days)::numeric,2) avg_backlog,
ROUND(SUM(actual_revenue)::numeric,2) total_revenue
FROM initiatives_scored
GROUP BY region
ORDER BY avg_aos DESC;
""",engine)

# ---------------- Owner ----------------
owner=pd.read_sql("""
SELECT
owner,
COUNT(DISTINCT initiative_id) initiatives,
ROUND(AVG(aos_health)::numeric,3) avg_aos,
ROUND(AVG(actual_otd_pct)::numeric,2) avg_otd,
ROUND(SUM(actual_revenue)::numeric,2) total_revenue
FROM initiatives_scored
GROUP BY owner
ORDER BY avg_aos DESC;
""",engine)

# ---------------- Lifecycle ----------------
lifecycle=pd.read_sql("""
SELECT *
FROM vw_lifecycle_analysis
ORDER BY avg_aos DESC;
""",engine)

executive.to_csv(OUTPUT_DIR/"executive_kpis.csv",index=False)
business.to_csv(OUTPUT_DIR/"business_unit_dashboard.csv",index=False)
region.to_csv(OUTPUT_DIR/"region_dashboard.csv",index=False)
owner.to_csv(OUTPUT_DIR/"owner_dashboard.csv",index=False)
lifecycle.to_csv(OUTPUT_DIR/"lifecycle_dashboard.csv",index=False)

print("\nGenerated files:")
for f in [
"executive_kpis.csv",
"business_unit_dashboard.csv",
"region_dashboard.csv",
"owner_dashboard.csv",
"lifecycle_dashboard.csv"
]:
    print(" -",OUTPUT_DIR/f)

print("\nExecutive KPIs:")
print(executive.to_string(index=False))

print("\nDone.")