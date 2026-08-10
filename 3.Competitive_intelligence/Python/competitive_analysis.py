import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR.parent / ".env"

load_dotenv(ENV_FILE)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# ============================================================
# 2. VALIDATE DATABASE CONFIGURATION
# ============================================================

required_variables = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME
}

missing = [
    key for key, value in required_variables.items()
    if not value
]

if missing:
    raise ValueError(
        f"Missing database environment variables: {missing}"
    )


# ============================================================
# 3. CREATE POSTGRESQL CONNECTION
# ============================================================

engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


# ============================================================
# 4. READ COMPETITIVE INTELLIGENCE VIEW
# ============================================================

print("=" * 80)
print("COMPETITIVE INTELLIGENCE ANALYSIS")
print("=" * 80)

query = """
SELECT *
FROM competitive_intelligence_summary
ORDER BY
    CASE
        WHEN market_share_rank IS NULL THEN 99
        ELSE market_share_rank
    END,
    price_gap_pct;
"""

df = pd.read_sql(query, engine)

print(f"\nRows loaded: {len(df)}")
print("\nCompetitive Intelligence Data:")
print(df)


# ============================================================
# 5. BASIC DATA VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("DATA VALIDATION")
print("=" * 80)

print("\nMissing values:")
print(df.isnull().sum())

print("\nData types:")
print(df.dtypes)


# ============================================================
# 6. IDENTIFY GROWTH OPPORTUNITIES
# ============================================================

growth_opportunities = df[
    df["strategic_action"] == "Growth Opportunity"
].copy()

print("\n" + "=" * 80)
print("GROWTH OPPORTUNITIES")
print("=" * 80)

print(growth_opportunities[
    [
        "product_family",
        "pall_price",
        "competitor_avg_price",
        "price_gap_pct",
        "market_share_pct",
        "market_share_rank"
    ]
])


# ============================================================
# 7. IDENTIFY POTENTIAL PRICE ADVANTAGES
# ============================================================

price_advantages = df[
    df["strategic_action"] == "Potential Price Advantage"
].copy()

print("\n" + "=" * 80)
print("POTENTIAL PRICE ADVANTAGES")
print("=" * 80)

print(price_advantages[
    [
        "product_family",
        "pall_price",
        "competitor_avg_price",
        "price_gap_pct"
    ]
])


# ============================================================
# 8. IDENTIFY PRODUCTS REQUIRING MONITORING
# ============================================================

monitor_pricing = df[
    df["strategic_action"] == "Monitor Pricing"
].copy()

print("\n" + "=" * 80)
print("PRODUCTS REQUIRING PRICING MONITORING")
print("=" * 80)

print(monitor_pricing[
    [
        "product_family",
        "pall_price",
        "competitor_avg_price",
        "price_gap_pct"
    ]
])


# ============================================================
# 9. CREATE EXECUTIVE SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("EXECUTIVE SUMMARY")
print("=" * 80)

print(
    f"\nTotal product families analyzed: {len(df)}"
)

print(
    f"Growth opportunities: {len(growth_opportunities)}"
)

print(
    f"Potential price advantages: {len(price_advantages)}"
)

print(
    f"Products requiring monitoring: {len(monitor_pricing)}"
)


# ============================================================
# 10. EXPORT RESULTS
# ============================================================

OUTPUT_DIR = BASE_DIR.parent / "Outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "competitive_intelligence_summary.csv"

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nCompetitive Intelligence output saved to:"
    f"\n{OUTPUT_FILE}"
)


# ============================================================
# 11. EXPORT GROWTH OPPORTUNITIES
# ============================================================

GROWTH_FILE = OUTPUT_DIR / "competitive_growth_opportunities.csv"

growth_opportunities.to_csv(
    GROWTH_FILE,
    index=False
)

print(
    f"\nGrowth opportunities saved to:"
    f"\n{GROWTH_FILE}"
)


# ============================================================
# 12. FINAL MESSAGE
# ============================================================

print("\n" + "=" * 80)
print("COMPETITIVE INTELLIGENCE ANALYSIS COMPLETE")
print("=" * 80)