import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine=create_engine(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

pricing=pd.read_sql("SELECT * FROM competitor_pricing",engine)

pricing["recommendation"]="Maintain"

pricing.loc[
pricing.avg_price_usd<
pricing.avg_price_usd.mean(),
"recommendation"
]="Increase Price"

pricing.loc[
pricing.avg_price_usd>
pricing.avg_price_usd.mean()*1.05,
"recommendation"
]="Reduce Price"

pricing.to_sql(
"pricing_recommendations",
engine,
if_exists="replace",
index=False
)

print("Recommendations created")