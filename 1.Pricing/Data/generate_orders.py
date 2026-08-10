import numpy as np
import pandas as pd


# ============================================================
# 1. SETTINGS
# ============================================================

np.random.seed(42)

business_units = [
    "Biopharma Consumables",
    "Medical",
    "Industrial",
    "Food & Beverage"
]

regions = [
    "North America",
    "EMEA",
    "APAC"
]

channels = [
    "Direct",
    "Distributor"
]

tiers = [
    "Strategic",
    "Standard",
    "Transactional"
]

quarters = pd.period_range(
    start="2024Q1",
    end="2025Q4",
    freq="Q"
)


# ============================================================
# 2. CREATE SKU MASTER
# ============================================================

skus = []

for bu in business_units:

    for i in range(10):

        skus.append({
            "business_unit": bu,
            "sku": f"{bu[:3].upper()}-{i + 1:03d}",
            "base_list_price": np.random.uniform(150, 4500)
        })

sku_df = pd.DataFrame(skus)


# ============================================================
# 3. GENERATE ORDERS
# ============================================================

rows = []
order_id = 1


for q_idx, q in enumerate(quarters):

    # --------------------------------------------------------
    # General market price inflation
    # --------------------------------------------------------

    market_price_factor = 1 + (0.06 * q_idx / 7)


    for _, sku in sku_df.iterrows():

        # ----------------------------------------------------
        # Number of orders for this SKU in this quarter
        # ----------------------------------------------------

        number_of_orders = np.random.poisson(15)


        for _ in range(number_of_orders):

            # ------------------------------------------------
            # Customer characteristics
            # ------------------------------------------------

            region = np.random.choice(
                regions,
                p=[0.40, 0.35, 0.25]
            )

            channel = np.random.choice(
                channels,
                p=[0.55, 0.45]
            )

            tier = np.random.choice(
                tiers,
                p=[0.20, 0.50, 0.30]
            )


            # ------------------------------------------------
            # LIST PRICE
            # ------------------------------------------------

            # Biopharma Consumables is deliberately kept
            # relatively flat so that we can later compare
            # its pricing against the rising PPI index.

            if sku["business_unit"] == "Biopharma Consumables":

                list_price = sku["base_list_price"]

            else:

                list_price = (
                    sku["base_list_price"]
                    * market_price_factor
                )


            # ------------------------------------------------
            # DISCOUNT
            # ------------------------------------------------

            tier_discount = {
                "Strategic": 0.18,
                "Standard": 0.10,
                "Transactional": 0.06
            }[tier]

            channel_discount = (
                0.04
                if channel == "Distributor"
                else 0
            )

            # APAC experiences slightly more discount pressure
            # over time.

            regional_discount_pressure = (
                0.03 * q_idx / 7
                if region == "APAC"
                else 0.01 * q_idx / 7
            )

            random_discount_noise = np.random.normal(
                0,
                0.015
            )

            discount_pct = np.clip(
                tier_discount
                + channel_discount
                + regional_discount_pressure
                + random_discount_noise,
                0.02,
                0.45
            )


            # ------------------------------------------------
            # NET PRICE
            # ------------------------------------------------

            net_price = (
                list_price
                * (1 - discount_pct)
            )


            # ------------------------------------------------
            # QUANTITY DEMAND
            # ------------------------------------------------

            # Base demand differs by customer type.

            tier_demand = {
                "Strategic": 1.25,
                "Standard": 1.00,
                "Transactional": 0.80
            }[tier]

            channel_demand = {
                "Direct": 1.05,
                "Distributor": 1.15
            }[channel]

            region_demand = {
                "North America": 1.10,
                "EMEA": 1.00,
                "APAC": 0.90
            }[region]


            # ------------------------------------------------
            # PRICE ELASTICITY
            # ------------------------------------------------

            # Higher prices should generally reduce demand.
            #
            # This is the key addition for the elasticity model.
            #
            # elasticity = -0.75 means:
            #
            # approximately 1% higher price
            # -> approximately 0.75% lower quantity
            #
            # before accounting for random demand variation.

            price_elasticity = -0.75

            base_quantity = 60

            price_effect = (
                net_price
                / sku["base_list_price"]
            ) ** price_elasticity


            # ------------------------------------------------
            # TIME TREND
            # ------------------------------------------------

            # Demand grows modestly over time.

            time_growth = (
                1 + 0.025 * q_idx
            )


            # ------------------------------------------------
            # RANDOM DEMAND VARIATION
            # ------------------------------------------------

            demand_noise = np.random.lognormal(
                mean=0,
                sigma=0.20
            )


            expected_quantity = (
                base_quantity
                * tier_demand
                * channel_demand
                * region_demand
                * price_effect
                * time_growth
                * demand_noise
            )


            # Convert expected demand into an integer order quantity.

            quantity = max(
                1,
                int(np.random.poisson(expected_quantity))
            )


            # ------------------------------------------------
            # REVENUE
            # ------------------------------------------------

            revenue = (
                net_price
                * quantity
            )


            # ------------------------------------------------
            # SAVE ORDER
            # ------------------------------------------------

            rows.append({

                "order_id":
                    f"ORD-{order_id:06d}",

                "order_date":
                    str(q.start_time.date()),

                "business_unit":
                    sku["business_unit"],

                "sku":
                    sku["sku"],

                "region":
                    region,

                "channel":
                    channel,

                "customer_tier":
                    tier,

                "list_price":
                    round(list_price, 2),

                "net_price":
                    round(net_price, 2),

                "discount_pct":
                    round(discount_pct * 100, 2),

                "quantity":
                    quantity,

                "revenue":
                    round(revenue, 2)
            })

            order_id += 1


# ============================================================
# 4. CREATE DATAFRAME
# ============================================================

orders_df = pd.DataFrame(rows)


# ============================================================
# 5. SAVE CSV
# ============================================================

orders_df.to_csv(
    "orders.csv",
    index=False
)


# ============================================================
# 6. BASIC VALIDATION
# ============================================================

print("\nOrder generation complete.")

print(
    f"Rows generated: {len(orders_df):,}"
)

print(
    f"Columns generated: {len(orders_df.columns)}"
)

print(
    "\nColumns:"
)

print(
    orders_df.columns.tolist()
)

print(
    "\nDate range:"
)

print(
    orders_df["order_date"].min(),
    "to",
    orders_df["order_date"].max()
)

print(
    "\nBusiness units:"
)

print(
    orders_df["business_unit"].value_counts()
)

print(
    "\nAverage discount:"
)

print(
    f"{orders_df['discount_pct'].mean():.2f}%"
)

print(
    "\nAverage net price:"
)

print(
    f"${orders_df['net_price'].mean():,.2f}"
)

print(
    "\nAverage quantity:"
)

print(
    f"{orders_df['quantity'].mean():.2f}"
)

print(
    "\nTotal revenue:"
)

print(
    f"${orders_df['revenue'].sum():,.2f}"
)

print(
    "\nSaved to: orders.csv"
)