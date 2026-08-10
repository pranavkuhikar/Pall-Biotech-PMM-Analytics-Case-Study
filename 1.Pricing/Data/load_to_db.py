import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

orders = pd.read_csv("orders.csv")
orders.to_sql(
    "orders",
    engine,
    if_exists="replace",
    index=False
)

ppi = pd.read_csv("ppi_index.csv")
ppi.to_sql(
    "raw_material_index",
    engine,
    if_exists="replace",
    index=False
)

print("Orders:", len(orders))
print("PPI:", len(ppi))