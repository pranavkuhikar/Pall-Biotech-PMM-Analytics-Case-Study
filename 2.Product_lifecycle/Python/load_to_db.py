import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ============================================================
# FILE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"

INPUT_FILE = DATA_DIR / "initiatives_scored.csv"

# ============================================================
# LOAD CSV
# ============================================================

print("=" * 80)
print("LOADING PRODUCT LIFECYCLE DATA")
print("=" * 80)

print(f"\nReading:\n{INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

print(f"\nRows loaded from CSV : {len(df):,}")
print(f"Columns             : {len(df.columns)}")

# ============================================================
# LOAD TO POSTGRES
# ============================================================

TABLE_NAME = "initiatives_scored"

print(f"\nUploading to PostgreSQL table '{TABLE_NAME}'...")

df.to_sql(
    TABLE_NAME,
    engine,
    if_exists="replace",
    index=False
)

print("Upload successful.")

# ============================================================
# VERIFY
# ============================================================

with engine.connect() as conn:

    row_count = conn.execute(
        text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    ).scalar()

    print(f"\nRows in PostgreSQL : {row_count:,}")

    sample = pd.read_sql(
        f"SELECT * FROM {TABLE_NAME} LIMIT 5",
        conn
    )

print("\nSample Data\n")
print(sample)

print("\nColumn Names\n")
print(list(df.columns))

print("\n" + "=" * 80)
print("PRODUCT LIFECYCLE DATA SUCCESSFULLY LOADED")
print("=" * 80)