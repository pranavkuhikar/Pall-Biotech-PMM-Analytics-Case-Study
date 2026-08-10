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
# 2. CREATE DATABASE CONNECTION
# ============================================================

engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/"
    f"{DB_NAME}"
)


# ============================================================
# 3. LOAD COMPETITIVE INTELLIGENCE DATA
# ============================================================

query = """
SELECT *
FROM competitive_intelligence_summary;
"""

df = pd.read_sql(query, engine)


# ============================================================
# 4. CALCULATE PRICING OPPORTUNITY
# ============================================================

df["potential_price_increase_usd"] = (
    df["competitor_avg_price"] - df["pall_price"]
)

df["potential_price_increase_pct"] = (
    (
        df["competitor_avg_price"]
        - df["pall_price"]
    )
    / df["pall_price"]
) * 100


# ============================================================
# 5. DETERMINE PRICING RECOMMENDATION
# ============================================================

def pricing_recommendation(row):

    if row["price_gap_pct"] <= -0.5:
        return "Consider Price Increase"

    elif row["price_gap_pct"] < 0:
        return "Evaluate Moderate Price Increase"

    elif row["price_gap_pct"] == 0:
        return "Maintain Price"

    else:
        return "Avoid Further Price Increase"


df["pricing_recommendation"] = df.apply(
    pricing_recommendation,
    axis=1
)


# ============================================================
# 6. CALCULATE MARKET POSITION SIGNAL
# ============================================================

def market_signal(row):

    if pd.isna(row["market_share_rank"]):
        return "Market Share Data Unavailable"

    elif row["market_share_rank"] <= 2:
        return "Strong Market Position"

    elif row["market_share_rank"] == 3:
        return "Growth Required"

    else:
        return "Weak Market Position"


df["market_position_signal"] = df.apply(
    market_signal,
    axis=1
)


# ============================================================
# 7. COMBINE PRICE + MARKET SIGNAL
# ============================================================

def strategic_recommendation(row):

    if (
        row["price_gap_pct"] < 0
        and row["market_share_rank"] == 3
    ):
        return "Increase Price Carefully While Defending Share"

    elif (
        row["price_gap_pct"] < 0
        and pd.isna(row["market_share_rank"])
    ):
        return "Potential Pricing Headroom"

    elif row["price_gap_pct"] > 0:
        return "Maintain Pricing Discipline"

    else:
        return "Maintain Current Position"


df["strategic_recommendation"] = df.apply(
    strategic_recommendation,
    axis=1
)


# ============================================================
# 8. SELECT FINAL OUTPUT COLUMNS
# ============================================================

output_columns = [
    "product_family",
    "pall_price",
    "competitor_avg_price",
    "price_gap_usd",
    "price_gap_pct",
    "potential_price_increase_usd",
    "potential_price_increase_pct",
    "market_share_pct",
    "market_share_rank",
    "market_position",
    "pricing_recommendation",
    "market_position_signal",
    "strategic_recommendation"
]

final_df = df[output_columns].copy()


# ============================================================
# 9. DISPLAY RESULTS
# ============================================================

print("=" * 80)
print("PRICING OPPORTUNITY ANALYSIS")
print("=" * 80)

print(
    final_df.to_string(index=False)
)


# ============================================================
# 10. EXPORT RESULTS
# ============================================================

OUTPUT_DIR = BASE_DIR.parent / "Outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "pricing_opportunity_analysis.csv"
)

final_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 11. SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("KEY PRICING OPPORTUNITIES")
print("=" * 80)

opportunities = final_df[
    final_df["potential_price_increase_usd"] > 0
].sort_values(
    "potential_price_increase_usd",
    ascending=False
)

print(
    opportunities[
        [
            "product_family",
            "pall_price",
            "competitor_avg_price",
            "potential_price_increase_usd",
            "potential_price_increase_pct",
            "strategic_recommendation"
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 80)
print("OUTPUT SAVED")
print("=" * 80)

print(OUTPUT_FILE)