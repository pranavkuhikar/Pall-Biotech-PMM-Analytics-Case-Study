import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# ============================================================
# CONFIGURATION
# ============================================================

# Project structure:
#
# Pall-Biotech-PMM-Analytics-Case study/
#
# ├── .env
# ├── .venv/
# │
# └── 3.Competitive_intelligence/
#     ├── Data/
#     ├── Python/
#     │   └── competitive_intelligence_final.py
#     └── Outputs/
#
# This file is inside:
# 3.Competitive_intelligence/Python/


BASE_DIR = Path(__file__).resolve().parent.parent

# Main project directory
PROJECT_ROOT = BASE_DIR.parent

# Output directory
OUTPUT_DIR = BASE_DIR / "Outputs"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# ============================================================
# VALIDATE DATABASE CONFIGURATION
# ============================================================

required_variables = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME
}

missing_variables = [
    key
    for key, value in required_variables.items()
    if not value
]

if missing_variables:

    raise ValueError(
        f"Missing database environment variables: "
        f"{missing_variables}"
    )


# ============================================================
# CREATE DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL
)


# ============================================================
# LOAD FINAL COMPETITIVE INTELLIGENCE VIEW
# ============================================================

print("=" * 80)
print("COMPETITIVE INTELLIGENCE FINAL ANALYSIS")
print("=" * 80)

print(
    "\nLoading final_pricing_recommendation from PostgreSQL..."
)


query = """
SELECT
    product_family,
    pall_price,
    competitor_avg_price,
    price_gap_usd,
    price_gap_pct,
    market_share_pct,
    market_share_rank,
    market_position,
    strategic_action,
    pricing_recommendation,
    competitive_position,
    final_recommendation

FROM final_pricing_recommendation

ORDER BY

    CASE
        WHEN final_recommendation LIKE 'High Priority%' THEN 1
        WHEN final_recommendation LIKE 'Moderate Priority%' THEN 2
        WHEN final_recommendation LIKE 'Evaluate%' THEN 3
        ELSE 4
    END,

    product_family;
"""


# IMPORTANT:
# SQLAlchemy text() is used here to avoid the
# immutabledict / pandas / SQLAlchemy compatibility error.

with engine.connect() as conn:

    df = pd.read_sql(
        text(query),
        conn
    )


print(
    f"\nRows loaded: {len(df)}"
)


# ============================================================
# DISPLAY COMPETITIVE INTELLIGENCE DATA
# ============================================================

print("\n" + "=" * 80)
print("COMPETITIVE INTELLIGENCE DATA")
print("=" * 80)

print()

print(
    df.to_string(index=False)
)


# ============================================================
# CHECK FOR MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("MISSING VALUES")
print("=" * 80)

print()

print(
    df.isnull().sum()
)


# ============================================================
# CHECK DATA TYPES
# ============================================================

print("\n" + "=" * 80)
print("DATA TYPES")
print("=" * 80)

print()

print(
    df.dtypes
)


# ============================================================
# IDENTIFY PRICING OPPORTUNITIES
# ============================================================

pricing_opportunities = df[
    df["final_recommendation"].str.contains(
        "Price Increase|Pricing Headroom",
        case=False,
        na=False
    )
].copy()


print("\n" + "=" * 80)
print("PRICING OPPORTUNITIES")
print("=" * 80)

print()

if len(pricing_opportunities) > 0:

    print(
        pricing_opportunities[
            [
                "product_family",
                "pall_price",
                "competitor_avg_price",
                "price_gap_usd",
                "price_gap_pct",
                "market_share_pct",
                "market_share_rank",
                "final_recommendation"
            ]
        ].to_string(index=False)
    )

else:

    print(
        "No pricing opportunities identified."
    )


# ============================================================
# IDENTIFY HIGH-PRIORITY OPPORTUNITIES
# ============================================================

high_priority = df[
    df["final_recommendation"].str.contains(
        "High Priority",
        case=False,
        na=False
    )
].copy()


print("\n" + "=" * 80)
print("HIGH-PRIORITY PRICING OPPORTUNITIES")
print("=" * 80)

print()

if len(high_priority) > 0:

    print(
        high_priority[
            [
                "product_family",
                "pall_price",
                "competitor_avg_price",
                "price_gap_usd",
                "price_gap_pct",
                "market_share_pct",
                "market_share_rank",
                "final_recommendation"
            ]
        ].to_string(index=False)
    )

else:

    print(
        "No high-priority pricing opportunities identified."
    )


# ============================================================
# PRODUCTS REQUIRING PRICING DISCIPLINE
# ============================================================

monitor_products = df[
    df["final_recommendation"].str.contains(
        "Maintain|Hold",
        case=False,
        na=False
    )
].copy()


print("\n" + "=" * 80)
print("PRODUCTS REQUIRING PRICING DISCIPLINE")
print("=" * 80)

print()

if len(monitor_products) > 0:

    print(
        monitor_products[
            [
                "product_family",
                "pall_price",
                "competitor_avg_price",
                "price_gap_usd",
                "price_gap_pct",
                "final_recommendation"
            ]
        ].to_string(index=False)
    )

else:

    print(
        "No products identified."
    )


# ============================================================
# KEY METRICS
# ============================================================

total_products = len(df)


high_priority_count = len(
    high_priority
)


pricing_headroom_count = len(
    df[
        df["final_recommendation"].str.contains(
            "Pricing Headroom",
            case=False,
            na=False
        )
    ]
)


monitor_count = len(
    monitor_products
)


market_share_available = (
    df["market_share_pct"]
    .notna()
    .sum()
)


average_price_gap_pct = (
    df["price_gap_pct"]
    .mean()
)


print("\n" + "=" * 80)
print("KEY COMPETITIVE INTELLIGENCE METRICS")
print("=" * 80)

print()

print(
    f"Total product families analysed : "
    f"{total_products}"
)

print(
    f"High-priority opportunities     : "
    f"{high_priority_count}"
)

print(
    f"Pricing-headroom opportunities  : "
    f"{pricing_headroom_count}"
)

print(
    f"Products requiring monitoring   : "
    f"{monitor_count}"
)

print(
    f"Products with market-share data : "
    f"{market_share_available}"
)

print(
    f"Average price gap               : "
    f"{average_price_gap_pct:.2f}%"
)


# ============================================================
# SAVE COMPLETE FINAL OUTPUT
# ============================================================

FINAL_OUTPUT = (
    OUTPUT_DIR
    / "competitive_intelligence_final.csv"
)


df.to_csv(
    FINAL_OUTPUT,
    index=False
)


# ============================================================
# SAVE PRICING OPPORTUNITIES
# ============================================================

OPPORTUNITY_OUTPUT = (
    OUTPUT_DIR
    / "pricing_opportunities.csv"
)


pricing_opportunities.to_csv(
    OPPORTUNITY_OUTPUT,
    index=False
)


# ============================================================
# SAVE HIGH-PRIORITY OPPORTUNITIES
# ============================================================

HIGH_PRIORITY_OUTPUT = (
    OUTPUT_DIR
    / "high_priority_pricing_opportunities.csv"
)


high_priority.to_csv(
    HIGH_PRIORITY_OUTPUT,
    index=False
)


# ============================================================
# SAVE PRICING DISCIPLINE PRODUCTS
# ============================================================

MONITOR_OUTPUT = (
    OUTPUT_DIR
    / "pricing_discipline_products.csv"
)


monitor_products.to_csv(
    MONITOR_OUTPUT,
    index=False
)


# ============================================================
# PRINT OUTPUT LOCATIONS
# ============================================================

print("\n" + "=" * 80)
print("OUTPUT FILES")
print("=" * 80)

print(
    f"\nFinal competitive intelligence:"
    f"\n{FINAL_OUTPUT}"
)

print(
    f"\nPricing opportunities:"
    f"\n{OPPORTUNITY_OUTPUT}"
)

print(
    f"\nHigh-priority opportunities:"
    f"\n{HIGH_PRIORITY_OUTPUT}"
)

print(
    f"\nPricing discipline products:"
    f"\n{MONITOR_OUTPUT}"
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 80)
print("COMPETITIVE INTELLIGENCE ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 80)