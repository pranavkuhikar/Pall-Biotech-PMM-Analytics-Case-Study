"""
robustness_analysis.py

Price elasticity robustness analysis for the Pall PMM case study.

Runs multiple elasticity specifications and saves a common robustness
results CSV for downstream pricing scenario analysis.
"""

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


# ======================================================================
# PATHS
# ======================================================================

# Folder containing this script
# .../Pall-Biotech-PMM-Analytics-Case study/1.Pricing/Outputs
SCRIPT_DIR = Path(__file__).resolve().parent

# Go back to the Pricing folder
# .../1.Pricing
PRICING_DIR = SCRIPT_DIR.parent

# Data folder
DATA_DIR = PRICING_DIR / "Data"

# Input files
ORDERS_FILE = DATA_DIR / "orders.csv"

# Support multiple possible PPI locations
PPI_ALTERNATIVES = [
    DATA_DIR / "ppi_index.csv",
    DATA_DIR / "ppi_index" / "ppi_index.csv",
    DATA_DIR / "ppi" / "ppi_index.csv",
]

# Output folder
OUTPUT_DIR = SCRIPT_DIR / "robustness"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
ROBUSTNESS_RESULTS_FILE = (
    OUTPUT_DIR / "robustness_results.csv"
)

ROBUSTNESS_RESULTS_SUMMARY_FILE = (
    OUTPUT_DIR / "robustness_results_summary.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR / "robustness_summary.txt"
)



# ============================================================
# DEBUG PATHS
# ============================================================

print("=" * 80)
print("PATH CHECK")
print("=" * 80)

print("SCRIPT_DIR :", SCRIPT_DIR)
print("PRICING_DIR:", PRICING_DIR)
print("DATA_DIR   :", DATA_DIR)
print("ORDERS_FILE:", ORDERS_FILE)
print("OUTPUT_DIR :", OUTPUT_DIR)

print("\nExists?")
print("orders.csv :", ORDERS_FILE.exists())

ppi_file = None
for candidate in PPI_ALTERNATIVES:
    print(candidate, "->", candidate.exists())
    if candidate.exists():
        ppi_file = candidate

print("=" * 80)


# ======================================================================
# HELPERS
# ======================================================================

def find_file(candidates):
    """Return the first existing file from a list of candidates."""
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def find_ppi_file():
    """Locate the PPI file."""

    ppi_file = find_file(PPI_ALTERNATIVES)

    if ppi_file is None:
        raise FileNotFoundError(
            "\nCould not find the PPI file.\n"
            "Checked:\n"
            + "\n".join(str(x) for x in PPI_ALTERNATIVES)
        )

    return ppi_file


def load_orders():
    """Load and clean order-level data."""

    print("Loading orders from:")
    print(ORDERS_FILE)

    if not ORDERS_FILE.exists():
        raise FileNotFoundError(
            f"\nOrders file not found:\n{ORDERS_FILE}"
        )

    orders = pd.read_csv(ORDERS_FILE)

    orders.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in orders.columns
    ]

    # --------------------------------------------------------------
    # Identify expected columns
    # --------------------------------------------------------------

    date_candidates = [
        "order_date",
        "date",
        "orderdate",
    ]

    sku_candidates = [
        "sku",
        "product_sku",
    ]

    quantity_candidates = [
        "quantity",
        "qty",
        "order_quantity",
    ]

    net_price_candidates = [
        "net_price",
        "netprice",
        "selling_price",
        "price",
    ]

    list_price_candidates = [
        "list_price",
        "listprice",
    ]

    discount_candidates = [
        "discount_pct",
        "discount",
        "discount_percent",
    ]

    region_candidates = ["region"]
    channel_candidates = ["channel"]
    tier_candidates = [
        "customer_tier",
        "customer_segment",
        "tier",
    ]

    def find_column(candidates, required=True):
        for candidate in candidates:
            if candidate in orders.columns:
                return candidate

        if required:
            raise ValueError(
                "Could not find required column.\n"
                f"Expected one of: {candidates}\n"
                f"Available columns: {list(orders.columns)}"
            )

        return None

    date_col = find_column(date_candidates)
    sku_col = find_column(sku_candidates)
    quantity_col = find_column(quantity_candidates)
    net_price_col = find_column(net_price_candidates)

    list_price_col = find_column(
        list_price_candidates,
        required=False
    )

    discount_col = find_column(
        discount_candidates,
        required=False
    )

    region_col = find_column(
        region_candidates,
        required=False
    )

    channel_col = find_column(
        channel_candidates,
        required=False
    )

    tier_col = find_column(
        tier_candidates,
        required=False
    )

    # --------------------------------------------------------------
    # Standardise names
    # --------------------------------------------------------------

    rename_map = {
        date_col: "order_date",
        sku_col: "sku",
        quantity_col: "quantity",
        net_price_col: "net_price",
    }

    if list_price_col:
        rename_map[list_price_col] = "list_price"

    if discount_col:
        rename_map[discount_col] = "discount_pct"

    if region_col:
        rename_map[region_col] = "region"

    if channel_col:
        rename_map[channel_col] = "channel"

    if tier_col:
        rename_map[tier_col] = "customer_tier"

    orders = orders.rename(columns=rename_map)

    # --------------------------------------------------------------
    # Convert types
    # --------------------------------------------------------------

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    orders["quantity"] = pd.to_numeric(
        orders["quantity"],
        errors="coerce"
    )

    orders["net_price"] = pd.to_numeric(
        orders["net_price"],
        errors="coerce"
    )

    if "list_price" in orders.columns:
        orders["list_price"] = pd.to_numeric(
            orders["list_price"],
            errors="coerce"
        )

    if "discount_pct" in orders.columns:
        orders["discount_pct"] = pd.to_numeric(
            orders["discount_pct"],
            errors="coerce"
        )

    # --------------------------------------------------------------
    # Remove invalid observations
    # --------------------------------------------------------------

    orders = orders.dropna(
        subset=[
            "order_date",
            "sku",
            "quantity",
            "net_price",
        ]
    )

    orders = orders[
        (orders["quantity"] > 0)
        & (orders["net_price"] > 0)
    ].copy()

    # --------------------------------------------------------------
    # Add time variable
    # --------------------------------------------------------------

    orders["quarter"] = (
        orders["order_date"]
        .dt.to_period("Q")
        .astype(str)
    )

    # --------------------------------------------------------------
    # Default categorical values
    # --------------------------------------------------------------

    for column in [
        "region",
        "channel",
        "customer_tier",
    ]:
        if column not in orders.columns:
            orders[column] = "Unknown"

        orders[column] = orders[column].fillna("Unknown").astype(str)

    # --------------------------------------------------------------
    # Log variables
    # --------------------------------------------------------------

    orders["log_quantity"] = np.log(orders["quantity"])
    orders["log_net_price"] = np.log(orders["net_price"])

    return orders


def load_ppi():
    """Load and prepare PPI data."""

    ppi_file = find_ppi_file()

    print("\nLoading PPI from:")
    print(ppi_file)

    ppi = pd.read_csv(ppi_file)

    ppi.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in ppi.columns
    ]

    # Find date column.
    date_candidates = [
        "observation_date",
        "date",
        "observationdate",
    ]

    date_col = None

    for candidate in date_candidates:
        if candidate in ppi.columns:
            date_col = candidate
            break

    if date_col is None:
        raise ValueError(
            "Could not find PPI date column.\n"
            f"Available columns: {list(ppi.columns)}"
        )

    value_candidates = [
        col
        for col in ppi.columns
        if col != date_col
    ]

    if not value_candidates:
        raise ValueError("Could not find PPI value column.")

    value_col = value_candidates[0]

    ppi = ppi.rename(
        columns={
            date_col: "observation_date",
            value_col: "ppi",
        }
    )

    ppi["observation_date"] = pd.to_datetime(
        ppi["observation_date"],
        errors="coerce"
    )

    ppi["ppi"] = pd.to_numeric(
        ppi["ppi"],
        errors="coerce"
    )

    ppi = ppi.dropna(
        subset=[
            "observation_date",
            "ppi",
        ]
    )

    # Convert monthly PPI into quarterly averages.
    ppi["quarter"] = (
        ppi["observation_date"]
        .dt.to_period("Q")
        .astype(str)
    )

    ppi_quarterly = (
        ppi.groupby("quarter", as_index=False)["ppi"]
        .mean()
    )

    ppi_quarterly["log_ppi"] = np.log(
        ppi_quarterly["ppi"]
    )

    return ppi_quarterly


def prepare_data(orders, ppi):
    """Merge order data with quarterly PPI."""

    data = orders.merge(
        ppi[
            [
                "quarter",
                "ppi",
                "log_ppi",
            ]
        ],
        on="quarter",
        how="left",
    )

    data = data.dropna(
        subset=[
            "ppi",
            "log_ppi",
        ]
    ).copy()

    return data


# ======================================================================
# MODELING
# ======================================================================

def fit_model(
    data,
    formula,
    model_name,
    cluster_column="sku",
):
    """Fit an OLS model with clustered standard errors."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        model = smf.ols(
            formula=formula,
            data=data,
        ).fit(
            cov_type="cluster",
            cov_kwds={
                "groups": data[cluster_column]
            },
        )

    coefficient = model.params.get(
        "log_net_price",
        np.nan
    )

    p_value = model.pvalues.get(
        "log_net_price",
        np.nan
    )

    confidence_interval = model.conf_int()

    if "log_net_price" in confidence_interval.index:
        ci_low = confidence_interval.loc[
            "log_net_price", 0
        ]

        ci_high = confidence_interval.loc[
            "log_net_price", 1
        ]
    else:
        ci_low = np.nan
        ci_high = np.nan

    return {
        "model": model_name,
        "observations": int(model.nobs),
        "elasticity": coefficient,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "significant_5pct": bool(p_value < 0.05),
        "direction": (
            "negative"
            if coefficient < 0
            else "positive"
        ),
    }, model


# ======================================================================
# ROBUSTNESS SPECIFICATIONS
# ======================================================================

def run_models(data):
    """Run all robustness specifications."""

    results = []
    fitted_models = {}

    # --------------------------------------------------------------
    # 1. Baseline pooled OLS
    # --------------------------------------------------------------

    result, model = fit_model(
        data,
        """
        log_quantity ~ log_net_price
        """,
        "1. Baseline pooled OLS",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 2. SKU fixed effects
    # --------------------------------------------------------------

    result, model = fit_model(
        data,
        """
        log_quantity ~ log_net_price + C(sku)
        """,
        "2. SKU fixed effects",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 3. SKU + quarter fixed effects
    # --------------------------------------------------------------

    result, model = fit_model(
        data,
        """
        log_quantity
        ~ log_net_price
        + C(sku)
        + C(quarter)
        """,
        "3. SKU + quarter fixed effects",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 4. Full commercial controls
    # --------------------------------------------------------------

    result, model = fit_model(
        data,
        """
        log_quantity
        ~ log_net_price
        + C(sku)
        + C(quarter)
        + C(region)
        + C(channel)
        + C(customer_tier)
        """,
        "4. SKU + time + commercial controls",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 5. SKU + PPI + commercial controls
    # --------------------------------------------------------------

    result, model = fit_model(
        data,
        """
        log_quantity
        ~ log_net_price
        + log_ppi
        + C(sku)
        + C(region)
        + C(channel)
        + C(customer_tier)
        """,
        "5. SKU + PPI + commercial controls",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 6. Winsorised price and quantity
    # --------------------------------------------------------------

    winsor = data.copy()

    winsor["log_net_price"] = (
        winsor["log_net_price"]
        .clip(
            winsor["log_net_price"].quantile(0.01),
            winsor["log_net_price"].quantile(0.99),
        )
    )

    winsor["log_quantity"] = (
        winsor["log_quantity"]
        .clip(
            winsor["log_quantity"].quantile(0.01),
            winsor["log_quantity"].quantile(0.99),
        )
    )

    result, model = fit_model(
        winsor,
        """
        log_quantity
        ~ log_net_price
        + C(sku)
        + C(quarter)
        + C(region)
        + C(channel)
        + C(customer_tier)
        """,
        "6. Winsorised price and quantity",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 7. Exclude discounts > 30%
    # --------------------------------------------------------------

    if "list_price" in data.columns:

        discount_data = data.copy()

        discount_data["calculated_discount"] = (
            1
            - (
                discount_data["net_price"]
                / discount_data["list_price"]
            )
        ) * 100

        discount_data = discount_data[
            discount_data["calculated_discount"] <= 30
        ].copy()

        result, model = fit_model(
            discount_data,
            """
            log_quantity
            ~ log_net_price
            + C(sku)
            + C(quarter)
            + C(region)
            + C(channel)
            + C(customer_tier)
            """,
            "7. Excluding discounts above 30%",
        )

        results.append(result)
        fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 8. List-price sensitivity
    # --------------------------------------------------------------

    if "list_price" in data.columns:

        list_data = data[
            data["list_price"] > 0
        ].copy()

        list_data["log_list_price"] = np.log(
            list_data["list_price"]
        )

        # Use list price instead of observed net price.
        list_data["log_net_price"] = (
            list_data["log_list_price"]
        )

        result, model = fit_model(
            list_data,
            """
            log_quantity
            ~ log_net_price
            + C(sku)
            + C(quarter)
            + C(region)
            + C(channel)
            + C(customer_tier)
            """,
            "8. List-price sensitivity",
        )

        results.append(result)
        fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 9. Higher-revenue SKUs
    # --------------------------------------------------------------

    revenue = (
        data.groupby("sku")["net_price"]
        .sum()
        .sort_values(ascending=False)
    )

    top_skus = revenue.head(
        max(1, int(len(revenue) * 0.50))
    ).index

    high_revenue_data = data[
        data["sku"].isin(top_skus)
    ].copy()

    result, model = fit_model(
        high_revenue_data,
        """
        log_quantity
        ~ log_net_price
        + C(sku)
        + C(quarter)
        + C(region)
        + C(channel)
        + C(customer_tier)
        """,
        "9. Higher-revenue SKUs",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    # --------------------------------------------------------------
    # 10. Exclude bottom 5% quantity
    # --------------------------------------------------------------

    quantity_cutoff = data["quantity"].quantile(0.05)

    trimmed_data = data[
        data["quantity"] > quantity_cutoff
    ].copy()

    result, model = fit_model(
        trimmed_data,
        """
        log_quantity
        ~ log_net_price
        + C(sku)
        + C(quarter)
        + C(region)
        + C(channel)
        + C(customer_tier)
        """,
        "10. Excluding bottom 5% quantity observations",
    )

    results.append(result)
    fitted_models[result["model"]] = model

    return pd.DataFrame(results), fitted_models


# ======================================================================
# REPORTING
# ======================================================================

def print_results(results):
    """Print robustness table."""

    print("\n")
    print("=" * 110)
    print("ROBUSTNESS RESULTS")
    print("=" * 110)

    display_columns = [
        "model",
        "observations",
        "elasticity",
        "p_value",
        "ci_low",
        "ci_high",
        "r_squared",
        "adj_r_squared",
        "significant_5pct",
        "direction",
    ]

    print(
        results[display_columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print("\n")
    print(f"Valid specifications: {len(results)}")

    negative_count = (
        results["elasticity"] < 0
    ).sum()

    positive_count = (
        results["elasticity"] > 0
    ).sum()

    significant_negative = (
        (results["elasticity"] < 0)
        & (results["significant_5pct"])
    ).sum()

    print(
        f"Negative elasticity estimates: "
        f"{negative_count}"
    )

    print(
        f"Positive elasticity estimates: "
        f"{positive_count}"
    )

    print(
        f"Significant negative estimates: "
        f"{significant_negative}"
    )

    print(
        f"Median elasticity: "
        f"{results['elasticity'].median():.4f}"
    )

    print(
        f"Elasticity range: "
        f"{results['elasticity'].min():.4f} "
        f"to "
        f"{results['elasticity'].max():.4f}"
    )


def save_outputs(
    results,
    orders,
    ppi,
):
    """Save CSV and text outputs."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------------
    # Main results file
    # --------------------------------------------------------------

    results.to_csv(
        ROBUSTNESS_RESULTS_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Compatibility copy
    # --------------------------------------------------------------

    results.to_csv(
        ROBUSTNESS_RESULTS_SUMMARY_FILE,
        index=False,
    )

    # --------------------------------------------------------------
    # Detailed text report
    # --------------------------------------------------------------

    negative_count = (
        results["elasticity"] < 0
    ).sum()

    positive_count = (
        results["elasticity"] > 0
    ).sum()

    significant_negative = (
        (results["elasticity"] < 0)
        & (results["significant_5pct"])
    ).sum()

    report = []

    report.append(
        "PRICE ELASTICITY ROBUSTNESS ANALYSIS"
    )
    report.append("=" * 72)
    report.append("")

    report.append(
        f"Orders used: {len(orders):,}"
    )

    report.append(
        f"Date range: "
        f"{orders['order_date'].min().date()} "
        f"to "
        f"{orders['order_date'].max().date()}"
    )

    report.append(
        f"PPI range: "
        f"{ppi['ppi'].min():.2f} "
        f"to "
        f"{ppi['ppi'].max():.2f}"
    )

    report.append(
        f"Unique SKUs: {orders['sku'].nunique()}"
    )

    report.append(
        f"Unique regions: {orders['region'].nunique()}"
    )

    report.append(
        f"Unique channels: {orders['channel'].nunique()}"
    )

    report.append(
        f"Unique customer tiers: "
        f"{orders['customer_tier'].nunique()}"
    )

    report.append(
        f"Unique quarters: "
        f"{orders['quarter'].nunique()}"
    )

    report.append("")
    report.append("=" * 72)
    report.append("ROBUSTNESS RESULTS")
    report.append("=" * 72)
    report.append("")

    report.append(
        results.to_string(
            index=False,
            float_format=lambda x: f"{x:.6f}",
        )
    )

    report.append("")
    report.append("=" * 72)
    report.append("SUMMARY")
    report.append("=" * 72)
    report.append("")

    report.append(
        f"Valid specifications: {len(results)}"
    )

    report.append(
        f"Negative elasticity estimates: "
        f"{negative_count}"
    )

    report.append(
        f"Positive elasticity estimates: "
        f"{positive_count}"
    )

    report.append(
        f"Significant negative estimates: "
        f"{significant_negative}"
    )

    report.append(
        f"Median elasticity: "
        f"{results['elasticity'].median():.6f}"
    )

    report.append(
        f"Elasticity range: "
        f"{results['elasticity'].min():.6f} "
        f"to "
        f"{results['elasticity'].max():.6f}"
    )

    report.append("")
    report.append("=" * 72)
    report.append("INTERPRETATION")
    report.append("=" * 72)
    report.append("")

    if negative_count == len(results):

        report.append(
            "All tested specifications produce negative "
            "price elasticity estimates."
        )

        report.append(
            "This provides strong robustness evidence "
            "for a negative observed price-quantity "
            "relationship."
        )

    elif negative_count > positive_count:

        report.append(
            "Most tested specifications produce negative "
            "price elasticity estimates."
        )

    else:

        report.append(
            "The direction of the elasticity estimate "
            "is not fully robust across specifications."
        )

    report.append("")
    report.append(
        "IMPORTANT ECONOMETRIC LIMITATION:"
    )

    report.append(
        "These estimates are based on observational "
        "pricing data and should not automatically be "
        "interpreted as causal demand elasticity."
    )

    report.append(
        "Observed prices may be endogenous to customer "
        "type, product mix, negotiated contracts, "
        "demand conditions, sales strategy and other "
        "commercial factors."
    )

    report.append(
        "The robustness analysis tests whether the "
        "direction and magnitude of the observed "
        "relationship are sensitive to reasonable "
        "changes in model specification and sample."
    )

    report.append("")
    report.append(
        "FILES CREATED:"
    )

    report.append(
        str(ROBUSTNESS_RESULTS_FILE)
    )

    report.append(
        str(ROBUSTNESS_RESULTS_SUMMARY_FILE)
    )

    report.append(
        str(SUMMARY_FILE)
    )

    SUMMARY_FILE.write_text(
        "\n".join(report),
        encoding="utf-8",
    )


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("")
    print("=" * 72)
    print("PRICE ELASTICITY ROBUSTNESS ANALYSIS")
    print("=" * 72)
    print("")

    orders = load_orders()
    ppi = load_ppi()

    data = prepare_data(
        orders,
        ppi,
    )

    print("")
    print(
        f"Orders used: {len(data):,}"
    )

    print(
        f"Date range: "
        f"{data['order_date'].min().date()} "
        f"to "
        f"{data['order_date'].max().date()}"
    )

    print(
        f"PPI range: "
        f"{data['ppi'].min():.2f} "
        f"to "
        f"{data['ppi'].max():.2f}"
    )

    print(
        f"Unique SKUs: "
        f"{data['sku'].nunique()}"
    )

    print(
        f"Unique regions: "
        f"{data['region'].nunique()}"
    )

    print(
        f"Unique channels: "
        f"{data['channel'].nunique()}"
    )

    print(
        f"Unique customer tiers: "
        f"{data['customer_tier'].nunique()}"
    )

    print(
        f"Unique quarters: "
        f"{data['quarter'].nunique()}"
    )

    print("")
    print(
        "Running robustness specifications..."
    )

    results, fitted_models = run_models(data)

    print_results(results)

    save_outputs(
        results,
        data,
        ppi,
    )

    print("")
    print("=" * 72)
    print("OUTPUT SAVED")
    print("=" * 72)

    print("")
    print(
        "Main robustness CSV:"
    )

    print(
        ROBUSTNESS_RESULTS_FILE
    )

    print("")
    print(
        "Compatibility CSV:"
    )

    print(
        ROBUSTNESS_RESULTS_SUMMARY_FILE
    )

    print("")
    print(
        "Detailed report:"
    )

    print(
        SUMMARY_FILE
    )

    print("")
    print(
        "Robustness analysis complete."
    )


if __name__ == "__main__":
    main()