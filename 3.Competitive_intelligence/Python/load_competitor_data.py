import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")

files = {
    "competitor_pricing": os.path.join(DATA_DIR, "competitor_pricing.xlsx"),
    "market_share": os.path.join(DATA_DIR, "market_share.xlsx"),
    "industry_growth": os.path.join(DATA_DIR, "industry_growth.xlsx")
}

for table, file in files.items():

    print(f"\nLoading {file}")

    df = pd.read_excel(file)

    print(f"Rows loaded: {len(df)}")

    df.to_sql(
        table,
        engine,
        if_exists="replace",
        index=False
    )

    print(f"Loaded into PostgreSQL table: {table}")

print("\nCompetitive Intelligence data loaded successfully.")