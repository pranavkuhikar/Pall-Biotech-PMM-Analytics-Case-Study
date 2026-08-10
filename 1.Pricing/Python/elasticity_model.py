import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sqlalchemy import create_engine


# ============================================================
# 1. DATABASE CONNECTION
# ============================================================

DB_USER = "PRANAV"
DB_PASS = "pranav123456"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "pall_pmm_case_study"

engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ============================================================
# 2. LOAD ORDER DATA
# ============================================================

orders = pd.read_sql(
    """
    SELECT
        order_id,
        order_date,
        business_unit,
        sku,
        region,
        channel,
        customer_tier,
        net_price,
        quantity
    FROM orders
    """,
    engine
)


# ============================================================
# 3. LOAD PPI DATA
# ============================================================

ppi = pd.read_sql(
    """
    SELECT
        observation_date,
        "PCU325211325211" AS ppi_index
    FROM raw_material_index
    """,
    engine
)


# ============================================================
# 4. DATA PREPARATION
# ============================================================

orders["order_date"] = pd.to_datetime(orders["order_date"])
ppi["observation_date"] = pd.to_datetime(ppi["observation_date"])

orders = orders.dropna(
    subset=[
        "order_date",
        "business_unit",
        "sku",
        "region",
        "channel",
        "customer_tier",
        "net_price",
        "quantity"
    ]
)

ppi = ppi.dropna(subset=["observation_date", "ppi_index"])


# Keep only valid positive values for log transformation
orders = orders[
    (orders["net_price"] > 0) &
    (orders["quantity"] > 0)
].copy()


# ============================================================
# 5. MATCH ORDERS TO MONTHLY PPI
# ============================================================

orders["ppi_month"] = orders["order_date"].dt.to_period("M")
ppi["ppi_month"] = ppi["observation_date"].dt.to_period("M")

ppi_monthly = (
    ppi.sort_values("observation_date")
    .drop_duplicates("ppi_month", keep="last")
    [["ppi_month", "ppi_index"]]
)

orders = orders.merge(
    ppi_monthly,
    on="ppi_month",
    how="left"
)


# ============================================================
# 6. KEEP OBSERVATIONS WITH PPI
# ============================================================

orders = orders.dropna(subset=["ppi_index"]).copy()


# ============================================================
# 7. LOG TRANSFORMATIONS
# ============================================================

orders["log_quantity"] = np.log(orders["quantity"])
orders["log_net_price"] = np.log(orders["net_price"])
orders["log_ppi"] = np.log(orders["ppi_index"])


# ============================================================
# 8. QUARTER VARIABLE
# ============================================================

orders["quarter"] = (
    orders["order_date"]
    .dt.to_period("Q")
    .astype(str)
)


# ============================================================
# 9. BASIC DATA CHECKS
# ============================================================

print("=" * 70)
print("PRICE ELASTICITY ANALYSIS")
print("=" * 70)

print(f"\nOrders used: {len(orders):,}")
print(
    f"Date range: "
    f"{orders['order_date'].min().date()} "
    f"to "
    f"{orders['order_date'].max().date()}"
)

print(
    f"PPI range: "
    f"{orders['ppi_index'].min():.2f} "
    f"to "
    f"{orders['ppi_index'].max():.2f}"
)

print(f"Unique SKUs: {orders['sku'].nunique()}")
print(f"Unique regions: {orders['region'].nunique()}")
print(f"Unique channels: {orders['channel'].nunique()}")
print(f"Unique customer tiers: {orders['customer_tier'].nunique()}")
print(f"Unique quarters: {orders['quarter'].nunique()}")


# ============================================================
# 10. MODEL A
#
# SKU FIXED EFFECTS + QUARTER FIXED EFFECTS
#
# PPI deliberately excluded.
#
# Why?
# Quarter fixed effects already absorb common movements
# over time. Including PPI simultaneously creates strong
# multicollinearity because PPI itself is a time-series variable.
# ============================================================

print("\n" + "=" * 70)
print("MODEL A: SKU + QUARTER FIXED EFFECTS")
print("=" * 70)

formula_a = """
log_quantity ~
log_net_price
+ C(sku)
+ C(quarter)
+ C(region)
+ C(channel)
+ C(customer_tier)
"""

model_a = smf.ols(
    formula=formula_a,
    data=orders
).fit(
    cov_type="cluster",
    cov_kwds={"groups": orders["sku"]}
)


# ============================================================
# 11. MODEL B
#
# SKU FIXED EFFECTS + PPI
#
# Quarter fixed effects deliberately excluded.
#
# This allows PPI to capture common cost pressure over time.
# ============================================================

print("\n" + "=" * 70)
print("MODEL B: SKU FIXED EFFECTS + PPI")
print("=" * 70)

formula_b = """
log_quantity ~
log_net_price
+ log_ppi
+ C(sku)
+ C(region)
+ C(channel)
+ C(customer_tier)
"""

model_b = smf.ols(
    formula=formula_b,
    data=orders
).fit(
    cov_type="cluster",
    cov_kwds={"groups": orders["sku"]}
)


# ============================================================
# 12. EXTRACT KEY RESULTS
# ============================================================

price_coef_a = model_a.params["log_net_price"]
price_p_a = model_a.pvalues["log_net_price"]
price_ci_a = model_a.conf_int().loc["log_net_price"]

price_coef_b = model_b.params["log_net_price"]
price_p_b = model_b.pvalues["log_net_price"]
price_ci_b = model_b.conf_int().loc["log_net_price"]

ppi_coef_b = model_b.params["log_ppi"]
ppi_p_b = model_b.pvalues["log_ppi"]
ppi_ci_b = model_b.conf_int().loc["log_ppi"]


# ============================================================
# 13. MODEL COMPARISON
# ============================================================

comparison = pd.DataFrame(
    {
        "Model": [
            "A: SKU + Quarter FE",
            "B: SKU + PPI"
        ],
        "Price Elasticity": [
            price_coef_a,
            price_coef_b
        ],
        "Price P-Value": [
            price_p_a,
            price_p_b
        ],
        "R-Squared": [
            model_a.rsquared,
            model_b.rsquared
        ],
        "Adjusted R-Squared": [
            model_a.rsquared_adj,
            model_b.rsquared_adj
        ],
        "Observations": [
            int(model_a.nobs),
            int(model_b.nobs)
        ]
    }
)


# ============================================================
# 14. PRINT MODEL SUMMARIES
# ============================================================

print("\n")
print(model_a.summary())

print("\n")
print(model_b.summary())


# ============================================================
# 15. PRINT EXECUTIVE RESULTS
# ============================================================

print("\n" + "=" * 70)
print("MODEL A RESULTS")
print("=" * 70)

print(f"Price elasticity: {price_coef_a:.4f}")
print(f"Price p-value: {price_p_a:.4f}")
print(
    f"Price 95% CI: "
    f"{price_ci_a[0]:.4f} to {price_ci_a[1]:.4f}"
)
print(f"R-squared: {model_a.rsquared:.4f}")
print(f"Adjusted R-squared: {model_a.rsquared_adj:.4f}")


print("\n" + "=" * 70)
print("MODEL B RESULTS")
print("=" * 70)

print(f"Price elasticity: {price_coef_b:.4f}")
print(f"Price p-value: {price_p_b:.4f}")
print(
    f"Price 95% CI: "
    f"{price_ci_b[0]:.4f} to {price_ci_b[1]:.4f}"
)

print(f"PPI coefficient: {ppi_coef_b:.4f}")
print(f"PPI p-value: {ppi_p_b:.4f}")
print(
    f"PPI 95% CI: "
    f"{ppi_ci_b[0]:.4f} to {ppi_ci_b[1]:.4f}"
)

print(f"R-squared: {model_b.rsquared:.4f}")
print(f"Adjusted R-squared: {model_b.rsquared_adj:.4f}")


# ============================================================
# 16. INTERPRETATION
# ============================================================

print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

if price_coef_a < 0:
    direction_a = "negative"
else:
    direction_a = "positive"

if price_coef_b < 0:
    direction_b = "negative"
else:
    direction_b = "positive"

print(
    f"\nModel A estimates a {direction_a} price relationship "
    f"with elasticity of {price_coef_a:.4f}."
)

print(
    f"Model B estimates a {direction_b} price relationship "
    f"with elasticity of {price_coef_b:.4f}."
)


if price_p_a < 0.05:
    print(
        "\nModel A price coefficient is statistically significant "
        "at the 5% level."
    )
else:
    print(
        "\nModel A price coefficient is NOT statistically significant "
        "at the 5% level."
    )


if price_p_b < 0.05:
    print(
        "Model B price coefficient is statistically significant "
        "at the 5% level."
    )
else:
    print(
        "Model B price coefficient is NOT statistically significant "
        "at the 5% level."
    )


print(
    "\nIMPORTANT ECONOMETRIC LIMITATION:"
)

print(
    "These estimates describe associations in observational pricing data. "
    "They should not automatically be interpreted as causal demand elasticity."
)

print(
    "A positive price coefficient, if observed, can occur because pricing "
    "is endogenous to customer type, product mix, negotiated contracts, "
    "demand conditions, or other commercial factors."
)


# ============================================================
# 17. SCENARIO CALCULATION
# ============================================================

price_change = 0.01

quantity_change_a = price_coef_a * price_change * 100
quantity_change_b = price_coef_b * price_change * 100

print("\n" + "=" * 70)
print("1% PRICE CHANGE SCENARIO")
print("=" * 70)

print(
    f"\nModel A: A 1% increase in price is associated with "
    f"an estimated {quantity_change_a:.4f}% change in quantity."
)

print(
    f"Model B: A 1% increase in price is associated with "
    f"an estimated {quantity_change_b:.4f}% change in quantity."
)


# ============================================================
# 18. DIAGNOSTICS
# ============================================================

residuals_a = model_a.resid
influence_a = model_a.get_influence()

max_leverage_a = influence_a.hat_matrix_diag.max()
mean_abs_residual_a = np.mean(np.abs(residuals_a))
residual_std_a = np.std(residuals_a)

print("\n" + "=" * 70)
print("MODEL A DIAGNOSTICS")
print("=" * 70)

print(f"Maximum leverage: {max_leverage_a:.4f}")
print(f"Mean absolute residual: {mean_abs_residual_a:.4f}")
print(f"Residual standard deviation: {residual_std_a:.4f}")


# ============================================================
# 19. SAVE RESULTS
# ============================================================

output_dir = os.path.dirname(os.path.abspath(__file__))

summary_path = os.path.join(
    output_dir,
    "elasticity_summary.txt"
)

with open(summary_path, "w", encoding="utf-8") as f:

    f.write("PALL PMM PRICING ANALYTICS\n")
    f.write("PRICE ELASTICITY ANALYSIS\n")
    f.write("=" * 70 + "\n\n")

    f.write(f"Orders used: {len(orders):,}\n")
    f.write(
        f"Date range: "
        f"{orders['order_date'].min().date()} "
        f"to "
        f"{orders['order_date'].max().date()}\n"
    )

    f.write(
        f"PPI range: "
        f"{orders['ppi_index'].min():.2f} "
        f"to "
        f"{orders['ppi_index'].max():.2f}\n"
    )

    f.write(f"Unique SKUs: {orders['sku'].nunique()}\n")
    f.write(f"Unique quarters: {orders['quarter'].nunique()}\n\n")

    f.write("=" * 70 + "\n")
    f.write("MODEL A: SKU + QUARTER FIXED EFFECTS\n")
    f.write("=" * 70 + "\n\n")

    f.write(model_a.summary().as_text())

    f.write("\n\n")
    f.write(f"Price elasticity: {price_coef_a:.4f}\n")
    f.write(f"Price p-value: {price_p_a:.4f}\n")
    f.write(
        f"Price 95% CI: "
        f"{price_ci_a[0]:.4f} to {price_ci_a[1]:.4f}\n"
    )
    f.write(f"R-squared: {model_a.rsquared:.4f}\n")
    f.write(f"Adjusted R-squared: {model_a.rsquared_adj:.4f}\n")

    f.write("\n\n")
    f.write("=" * 70 + "\n")
    f.write("MODEL B: SKU FIXED EFFECTS + PPI\n")
    f.write("=" * 70 + "\n\n")

    f.write(model_b.summary().as_text())

    f.write("\n\n")
    f.write(f"Price elasticity: {price_coef_b:.4f}\n")
    f.write(f"Price p-value: {price_p_b:.4f}\n")
    f.write(
        f"Price 95% CI: "
        f"{price_ci_b[0]:.4f} to {price_ci_b[1]:.4f}\n"
    )

    f.write(f"PPI coefficient: {ppi_coef_b:.4f}\n")
    f.write(f"PPI p-value: {ppi_p_b:.4f}\n")
    f.write(
        f"PPI 95% CI: "
        f"{ppi_ci_b[0]:.4f} to {ppi_ci_b[1]:.4f}\n"
    )

    f.write(f"R-squared: {model_b.rsquared:.4f}\n")
    f.write(
        f"Adjusted R-squared: "
        f"{model_b.rsquared_adj:.4f}\n"
    )

    f.write("\n\n")
    f.write("=" * 70 + "\n")
    f.write("MODEL COMPARISON\n")
    f.write("=" * 70 + "\n\n")

    f.write(comparison.to_string(index=False))

    f.write("\n\n")
    f.write("=" * 70 + "\n")
    f.write("INTERPRETATION\n")
    f.write("=" * 70 + "\n\n")

    f.write(
        "The elasticity estimates represent associations observed "
        "in historical pricing data rather than experimentally identified "
        "causal effects.\n\n"
    )

    f.write(
        "Model A uses quarter fixed effects to control for common "
        "time-varying conditions. PPI is excluded because it is itself "
        "a time-varying variable and would overlap strongly with the "
        "quarter fixed effects.\n\n"
    )

    f.write(
        "Model B explicitly controls for PPI while omitting quarter "
        "fixed effects, allowing the raw-material index to capture "
        "common cost pressure.\n"
    )


print("\n" + "=" * 70)
print("OUTPUT SAVED")
print("=" * 70)

print(f"\nFull results saved to:")
print(summary_path)