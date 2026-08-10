"""
Pricing Scenario Analysis
=========================

Purpose
-------
Evaluate commercial pricing scenarios using the empirically estimated
price elasticity from the robustness analysis.

The script:
1. Loads order-level pricing data.
2. Loads robustness-analysis results.
3. Selects the preferred elasticity estimate.
4. Calculates baseline revenue.
5. Simulates price-change scenarios.
6. Estimates quantity response using constant elasticity.
7. Calculates revenue impact.
8. Calculates discount/revenue implications.
9. Produces SKU-level and business-unit-level scenario outputs.
10. Saves CSV files and a text summary.

Important econometric note
--------------------------
The elasticity estimate comes from observational pricing data. Therefore,
scenario outputs are decision-support estimates, not causal guarantees.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# ======================================================================
# PATHS
# ======================================================================

SCRIPT_DIR = Path(__file__).resolve().parent

PRICING_DIR = SCRIPT_DIR.parent

DATA_DIR = PRICING_DIR / "Data"

ORDERS_FILE = DATA_DIR / "orders.csv"

ROBUSTNESS_DIR = SCRIPT_DIR / "robustness"

OUTPUT_DIR = SCRIPT_DIR / "pricing_scenarios"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ======================================================================
# SCENARIO SETTINGS
# ======================================================================

PRICE_SCENARIOS = [-0.10, -0.05, -0.02, 0.00, 0.02, 0.05, 0.10]

# Preferred elasticity specification.
#
# From the robustness analysis:
# "4. SKU + time + commercial controls"
#
# This corresponds to the main econometric model used earlier.
PREFERRED_MODEL_KEYWORDS = [
    "SKU + time + commercial controls",
    "SKU + quarter fixed effects",
]

# If the preferred model cannot be found, use the median robustness
# elasticity rather than silently inventing an estimate.
USE_MEDIAN_IF_PREFERRED_MODEL_MISSING = True


# ======================================================================
# GENERAL HELPERS
# ======================================================================

def print_section(title):
    """Print a formatted console section."""
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def find_robustness_file():
    """
    Find the robustness results CSV.

    The robustness script may have produced either:
        robustness_results.csv
    or:
        robustness_results.csv / robustness_results.csv-like output

    We therefore search the robustness folder instead of assuming
    one exact filename.
    """

    candidates = [
        ROBUSTNESS_DIR / "robustness_results.csv",
        ROBUSTNESS_DIR / "robustness_results.csv",
        ROBUSTNESS_DIR / "robustness_analysis_results.csv",
        ROBUSTNESS_DIR / "robustness_results_summary.csv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    csv_files = list(ROBUSTNESS_DIR.glob("*.csv"))

    if len(csv_files) == 1:
        return csv_files[0]

    if len(csv_files) > 1:
        preferred = [
            f for f in csv_files
            if "robust" in f.name.lower()
        ]

        if len(preferred) == 1:
            return preferred[0]

        if preferred:
            return preferred[0]

    raise FileNotFoundError(
        "Could not find robustness results CSV.\n\n"
        f"Expected folder:\n{ROBUSTNESS_DIR}\n\n"
        "Run robustness_analysis.py first and confirm that a CSV "
        "file exists in this folder."
    )


# ======================================================================
# LOAD ORDERS
# ======================================================================

def load_orders():
    """Load and clean the order-level dataset."""

    print(f"Loading orders from:\n{ORDERS_FILE}")

    if not ORDERS_FILE.exists():
        raise FileNotFoundError(
            f"Orders file not found:\n{ORDERS_FILE}\n\n"
            "Check that orders.csv is located in:\n"
            f"{DATA_DIR}"
        )

    orders = pd.read_csv(ORDERS_FILE)

    orders.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in orders.columns
    ]

    # --------------------------------------------------------------
    # Detect important columns
    # --------------------------------------------------------------

    column_aliases = {
        "date": [
            "date",
            "order_date",
            "orderdate",
        ],
        "sku": [
            "sku",
            "product_id",
            "product",
        ],
        "quantity": [
            "quantity",
            "qty",
            "units",
        ],
        "net_price": [
            "net_price",
            "netprice",
            "price",
            "selling_price",
            "sell_price",
        ],
        "list_price": [
            "list_price",
            "listprice",
            "list_price_per_unit",
        ],
        "discount_pct": [
            "discount_pct",
            "discount",
            "discount_percent",
        ],
        "business_unit": [
            "business_unit",
            "businessunit",
            "business_unit_name",
        ],
        "region": [
            "region",
        ],
        "channel": [
            "channel",
        ],
        "customer_tier": [
            "customer_tier",
            "customer_segment",
            "tier",
        ],
    }

    resolved = {}

    for standard_name, aliases in column_aliases.items():
        for alias in aliases:
            if alias in orders.columns:
                resolved[standard_name] = alias
                break

    required = [
        "quantity",
        "net_price",
    ]

    missing = [
        column
        for column in required
        if column not in resolved
    ]

    if missing:
        raise ValueError(
            "Required columns are missing from orders.csv:\n"
            f"{missing}\n\n"
            f"Available columns:\n{list(orders.columns)}"
        )

    # --------------------------------------------------------------
    # Rename to standard names
    # --------------------------------------------------------------

    rename_map = {
        actual: standard
        for standard, actual in resolved.items()
    }

    orders = orders.rename(columns=rename_map)

    # --------------------------------------------------------------
    # Convert numeric fields
    # --------------------------------------------------------------

    numeric_columns = [
        "quantity",
        "net_price",
        "list_price",
        "discount_pct",
    ]

    for column in numeric_columns:
        if column in orders.columns:
            orders[column] = pd.to_numeric(
                orders[column],
                errors="coerce",
            )

    # --------------------------------------------------------------
    # Date
    # --------------------------------------------------------------

    if "date" in orders.columns:
        orders["date"] = pd.to_datetime(
            orders["date"],
            errors="coerce",
        )

    # --------------------------------------------------------------
    # Remove unusable observations
    # --------------------------------------------------------------

    orders = orders.dropna(
        subset=["quantity", "net_price"]
    )

    orders = orders[
        (orders["quantity"] > 0)
        & (orders["net_price"] > 0)
    ].copy()

    # --------------------------------------------------------------
    # Revenue
    # --------------------------------------------------------------

    orders["revenue"] = (
        orders["quantity"] *
        orders["net_price"]
    )

    # --------------------------------------------------------------
    # Discount
    # --------------------------------------------------------------

    if "list_price" in orders.columns:

        orders.loc[
            orders["list_price"] <= 0,
            "list_price"
        ] = np.nan

        orders["calculated_discount_pct"] = (
            1
            - orders["net_price"] / orders["list_price"]
        ) * 100

    elif "discount_pct" in orders.columns:

        orders["calculated_discount_pct"] = (
            orders["discount_pct"]
        )

    else:

        orders["calculated_discount_pct"] = np.nan

    return orders


# ======================================================================
# LOAD ROBUSTNESS RESULTS
# ======================================================================

def load_elasticity():
    """
    Load robustness results and select the preferred elasticity estimate.
    """

    robustness_file = find_robustness_file()

    print(
        f"\nLoading robustness results from:\n"
        f"{robustness_file}"
    )

    results = pd.read_csv(robustness_file)

    results.columns = [
        str(column).strip().lower()
        for column in results.columns
    ]

    required_columns = [
        "elasticity",
        "p_value",
    ]

    missing = [
        column
        for column in required_columns
        if column not in results.columns
    ]

    if missing:
        raise ValueError(
            "Robustness results are missing required columns:\n"
            f"{missing}\n\n"
            f"Available columns:\n{list(results.columns)}"
        )

    # --------------------------------------------------------------
    # Find preferred model
    # --------------------------------------------------------------

    selected_row = None

    if "model" in results.columns:

        for keyword in PREFERRED_MODEL_KEYWORDS:

            matches = results[
                results["model"]
                .astype(str)
                .str.contains(
                    keyword,
                    case=False,
                    regex=False,
                )
            ]

            if not matches.empty:

                selected_row = matches.iloc[0]

                print(
                    "\nPreferred elasticity model found:"
                )
                print(
                    selected_row["model"]
                )

                break

    # --------------------------------------------------------------
    # Fallback to median
    # --------------------------------------------------------------

    if selected_row is None:

        if not USE_MEDIAN_IF_PREFERRED_MODEL_MISSING:

            raise ValueError(
                "Preferred elasticity model could not be found "
                "in robustness results."
            )

        elasticity = pd.to_numeric(
            results["elasticity"],
            errors="coerce",
        ).dropna().median()

        p_value = np.nan

        model_name = "Median robustness elasticity"

        print(
            "\nPreferred model was not found."
        )

        print(
            f"Using median robustness elasticity: {elasticity:.4f}"
        )

    else:

        elasticity = float(
            selected_row["elasticity"]
        )

        p_value = float(
            selected_row["p_value"]
        )

        model_name = str(
            selected_row["model"]
        )

    if not np.isfinite(elasticity):

        raise ValueError(
            "Elasticity estimate is not valid."
        )

    return (
        elasticity,
        p_value,
        model_name,
        results,
        robustness_file,
    )


# ======================================================================
# BASELINE SUMMARY
# ======================================================================

def calculate_baseline(orders):
    """Calculate baseline commercial metrics."""

    total_revenue = orders["revenue"].sum()

    total_quantity = orders["quantity"].sum()

    weighted_avg_price = (
        total_revenue /
        total_quantity
    )

    order_count = len(orders)

    sku_count = (
        orders["sku"].nunique()
        if "sku" in orders.columns
        else np.nan
    )

    return {
        "orders": order_count,
        "quantity": total_quantity,
        "revenue": total_revenue,
        "weighted_avg_price": weighted_avg_price,
        "skus": sku_count,
    }


# ======================================================================
# SCENARIO CALCULATION
# ======================================================================

def calculate_scenario(
    orders,
    elasticity,
    price_change,
):
    """
    Calculate a constant-elasticity pricing scenario.

    Formula:

        Q1 / Q0 = (P1 / P0)^elasticity

    Therefore:

        Q1 = Q0 * (1 + price_change)^elasticity

    Revenue:

        R1 = P1 * Q1
    """

    price_multiplier = 1 + price_change

    if price_multiplier <= 0:

        raise ValueError(
            "Price change would result in a non-positive price."
        )

    quantity_multiplier = (
        price_multiplier ** elasticity
    )

    scenario = orders.copy()

    scenario["scenario_price"] = (
        scenario["net_price"] *
        price_multiplier
    )

    scenario["quantity_multiplier"] = (
        quantity_multiplier
    )

    scenario["scenario_quantity"] = (
        scenario["quantity"] *
        quantity_multiplier
    )

    scenario["scenario_revenue"] = (
        scenario["scenario_price"] *
        scenario["scenario_quantity"]
    )

    scenario["baseline_revenue"] = (
        scenario["revenue"]
    )

    scenario["revenue_change"] = (
        scenario["scenario_revenue"]
        - scenario["baseline_revenue"]
    )

    scenario["revenue_change_pct"] = np.where(
        scenario["baseline_revenue"] != 0,
        (
            scenario["revenue_change"]
            / scenario["baseline_revenue"]
        ) * 100,
        np.nan,
    )

    return scenario


# ======================================================================
# OVERALL SCENARIOS
# ======================================================================

def create_scenario_summary(
    orders,
    elasticity,
):
    """Create overall scenario table."""

    baseline = calculate_baseline(orders)

    rows = []

    for price_change in PRICE_SCENARIOS:

        price_multiplier = 1 + price_change

        quantity_multiplier = (
            price_multiplier ** elasticity
        )

        scenario_quantity = (
            baseline["quantity"]
            * quantity_multiplier
        )

        scenario_price = (
            baseline["weighted_avg_price"]
            * price_multiplier
        )

        scenario_revenue = (
            scenario_price
            * scenario_quantity
        )

        revenue_change = (
            scenario_revenue
            - baseline["revenue"]
        )

        revenue_change_pct = (
            revenue_change
            / baseline["revenue"]
        ) * 100

        quantity_change_pct = (
            quantity_multiplier - 1
        ) * 100

        rows.append({
            "price_change_pct": price_change * 100,
            "price_multiplier": price_multiplier,
            "quantity_change_pct": quantity_change_pct,
            "revenue_change_pct": revenue_change_pct,
            "baseline_revenue": baseline["revenue"],
            "scenario_revenue": scenario_revenue,
            "revenue_change": revenue_change,
        })

    return pd.DataFrame(rows)


# ======================================================================
# BUSINESS UNIT SCENARIOS
# ======================================================================

def create_business_unit_scenarios(
    orders,
    elasticity,
):
    """Create scenario analysis by business unit."""

    if "business_unit" not in orders.columns:

        return pd.DataFrame()

    rows = []

    for business_unit, group in orders.groupby(
        "business_unit"
    ):

        baseline_quantity = group["quantity"].sum()

        baseline_revenue = group["revenue"].sum()

        baseline_price = (
            baseline_revenue /
            baseline_quantity
        )

        for price_change in PRICE_SCENARIOS:

            price_multiplier = 1 + price_change

            quantity_multiplier = (
                price_multiplier ** elasticity
            )

            scenario_quantity = (
                baseline_quantity
                * quantity_multiplier
            )

            scenario_price = (
                baseline_price
                * price_multiplier
            )

            scenario_revenue = (
                scenario_price
                * scenario_quantity
            )

            revenue_change = (
                scenario_revenue
                - baseline_revenue
            )

            revenue_change_pct = (
                revenue_change
                / baseline_revenue
            ) * 100

            quantity_change_pct = (
                quantity_multiplier - 1
            ) * 100

            rows.append({
                "business_unit": business_unit,
                "price_change_pct": price_change * 100,
                "baseline_quantity": baseline_quantity,
                "baseline_revenue": baseline_revenue,
                "baseline_avg_price": baseline_price,
                "quantity_change_pct": quantity_change_pct,
                "scenario_quantity": scenario_quantity,
                "scenario_revenue": scenario_revenue,
                "revenue_change": revenue_change,
                "revenue_change_pct": revenue_change_pct,
            })

    return pd.DataFrame(rows)


# ======================================================================
# REGION SCENARIOS
# ======================================================================

def create_region_scenarios(
    orders,
    elasticity,
):
    """Create scenario analysis by region."""

    if "region" not in orders.columns:

        return pd.DataFrame()

    rows = []

    for region, group in orders.groupby(
        "region"
    ):

        baseline_quantity = group["quantity"].sum()

        baseline_revenue = group["revenue"].sum()

        baseline_price = (
            baseline_revenue /
            baseline_quantity
        )

        for price_change in PRICE_SCENARIOS:

            price_multiplier = 1 + price_change

            quantity_multiplier = (
                price_multiplier ** elasticity
            )

            scenario_quantity = (
                baseline_quantity
                * quantity_multiplier
            )

            scenario_price = (
                baseline_price
                * price_multiplier
            )

            scenario_revenue = (
                scenario_price
                * scenario_quantity
            )

            revenue_change = (
                scenario_revenue
                - baseline_revenue
            )

            revenue_change_pct = (
                revenue_change
                / baseline_revenue
            ) * 100

            rows.append({
                "region": region,
                "price_change_pct": price_change * 100,
                "baseline_revenue": baseline_revenue,
                "baseline_quantity": baseline_quantity,
                "scenario_quantity": scenario_quantity,
                "scenario_revenue": scenario_revenue,
                "revenue_change": revenue_change,
                "revenue_change_pct": revenue_change_pct,
            })

    return pd.DataFrame(rows)


# ======================================================================
# SKU SCENARIOS
# ======================================================================

def create_sku_scenarios(
    orders,
    elasticity,
):
    """Create scenario analysis by SKU."""

    if "sku" not in orders.columns:

        return pd.DataFrame()

    rows = []

    for sku, group in orders.groupby("sku"):

        baseline_quantity = group["quantity"].sum()

        baseline_revenue = group["revenue"].sum()

        baseline_price = (
            baseline_revenue /
            baseline_quantity
        )

        for price_change in PRICE_SCENARIOS:

            price_multiplier = 1 + price_change

            quantity_multiplier = (
                price_multiplier ** elasticity
            )

            scenario_quantity = (
                baseline_quantity
                * quantity_multiplier
            )

            scenario_price = (
                baseline_price
                * price_multiplier
            )

            scenario_revenue = (
                scenario_price
                * scenario_quantity
            )

            revenue_change = (
                scenario_revenue
                - baseline_revenue
            )

            revenue_change_pct = (
                revenue_change
                / baseline_revenue
            ) * 100

            quantity_change_pct = (
    quantity_multiplier - 1
) * 100

            rows.append({
    "sku": sku,
    "price_change_pct": price_change * 100,
    "baseline_quantity": baseline_quantity,
    "baseline_revenue": baseline_revenue,
    "baseline_avg_price": baseline_price,
    "quantity_change_pct": quantity_change_pct,
    "scenario_quantity": scenario_quantity,
    "scenario_revenue": scenario_revenue,
    "revenue_change": revenue_change,
    "revenue_change_pct": revenue_change_pct,
})

    return pd.DataFrame(rows)


# ======================================================================
# DISCOUNT IMPACT
# ======================================================================

def calculate_discount_implications(
    orders,
    elasticity,
):
    """
    Calculate current discount levels and potential implications.

    This is descriptive rather than causal.
    """

    if "calculated_discount_pct" not in orders.columns:

        return pd.DataFrame()

    data = orders.copy()

    valid = data[
        data["calculated_discount_pct"].notna()
    ].copy()

    if valid.empty:

        return pd.DataFrame()

    summary = (
        valid.groupby(
            "business_unit",
            dropna=False,
        )
        .agg(
            orders=("revenue", "size"),
            revenue=("revenue", "sum"),
            avg_discount_pct=(
                "calculated_discount_pct",
                "mean",
            ),
            median_discount_pct=(
                "calculated_discount_pct",
                "median",
            ),
            max_discount_pct=(
                "calculated_discount_pct",
                "max",
            ),
        )
        .reset_index()
    )

    return summary


# ======================================================================
# TEXT REPORT
# ======================================================================

def create_report(
    baseline,
    elasticity,
    p_value,
    model_name,
    scenario_summary,
    business_unit_summary,
    robustness_results,
):
    """Create a detailed text report."""

    lines = []

    lines.append("=" * 72)
    lines.append("PRICING SCENARIO ANALYSIS")
    lines.append("=" * 72)
    lines.append("")

    lines.append("BASELINE")
    lines.append("-" * 72)

    lines.append(
        f"Orders: {baseline['orders']:,}"
    )

    lines.append(
        f"Quantity: {baseline['quantity']:,.2f}"
    )

    lines.append(
        f"Revenue: {baseline['revenue']:,.2f}"
    )

    lines.append(
        f"Weighted average price: "
        f"{baseline['weighted_avg_price']:,.2f}"
    )

    lines.append(
        f"Unique SKUs: {baseline['skus']}"
    )

    lines.append("")

    lines.append("ELASTICITY INPUT")
    lines.append("-" * 72)

    lines.append(
        f"Selected model: {model_name}"
    )

    lines.append(
        f"Elasticity: {elasticity:.4f}"
    )

    if np.isfinite(p_value):

        lines.append(
            f"P-value: {p_value:.4f}"
        )

    lines.append("")

    lines.append(
        "INTERPRETATION"
    )

    lines.append("-" * 72)

    lines.append(
        "The scenario model uses a constant-elasticity relationship:"
    )

    lines.append(
        "Q1 / Q0 = (P1 / P0)^elasticity"
    )

    lines.append("")

    lines.append(
        "Because the selected elasticity is negative, "
        "a price increase produces a modeled reduction "
        "in quantity."
    )

    lines.append("")

    lines.append(
        "These scenarios are analytical estimates based on "
        "observational pricing data. They should not be "
        "interpreted as guaranteed causal outcomes."
    )

    lines.append("")

    lines.append(
        "SCENARIO RESULTS"
    )

    lines.append("-" * 72)

    for _, row in scenario_summary.iterrows():

        lines.append(
            f"Price change: "
            f"{row['price_change_pct']:+.0f}% | "
            f"Quantity change: "
            f"{row['quantity_change_pct']:+.2f}% | "
            f"Revenue change: "
            f"{row['revenue_change_pct']:+.2f}% | "
            f"Revenue impact: "
            f"{row['revenue_change']:,.2f}"
        )

    lines.append("")

    lines.append(
        "ROBUSTNESS CONTEXT"
    )

    lines.append("-" * 72)

    if "elasticity" in robustness_results.columns:

        valid_elasticities = pd.to_numeric(
            robustness_results["elasticity"],
            errors="coerce",
        ).dropna()

        lines.append(
            f"Valid elasticity specifications: "
            f"{len(valid_elasticities)}"
        )

        if not valid_elasticities.empty:

            lines.append(
                f"Median elasticity: "
                f"{valid_elasticities.median():.4f}"
            )

            lines.append(
                f"Minimum elasticity: "
                f"{valid_elasticities.min():.4f}"
            )

            lines.append(
                f"Maximum elasticity: "
                f"{valid_elasticities.max():.4f}"
            )

            negative_count = (
                valid_elasticities < 0
            ).sum()

            positive_count = (
                valid_elasticities > 0
            ).sum()

            lines.append(
                f"Negative estimates: "
                f"{negative_count}"
            )

            lines.append(
                f"Positive estimates: "
                f"{positive_count}"
            )

    lines.append("")

    lines.append(
        "RECOMMENDATION FRAMEWORK"
    )

    lines.append("-" * 72)

    lines.append(
        "1. Use modest price increases as the primary "
        "test scenario rather than relying on extreme changes."
    )

    lines.append(
        "2. Prioritise SKUs and business units where modeled "
        "revenue uplift is large and commercial risk is manageable."
    )

    lines.append(
        "3. Validate scenarios through controlled pricing tests "
        "before implementing broad price changes."
    )

    lines.append(
        "4. Monitor quantity, revenue, discounting and customer "
        "retention after implementation."
    )

    lines.append(
        "5. Treat the elasticity estimate as a planning parameter, "
        "not a causal truth."
    )

    return "\n".join(lines)


# ======================================================================
# MAIN
# ======================================================================

def main():

    print_section(
        "PRICING SCENARIO ANALYSIS"
    )

    # --------------------------------------------------------------
    # Load data
    # --------------------------------------------------------------

    orders = load_orders()

    (
        elasticity,
        p_value,
        model_name,
        robustness_results,
        robustness_file,
    ) = load_elasticity()

    print()

    print(
        f"Orders used: {len(orders):,}"
    )

    if "date" in orders.columns:

        valid_dates = orders["date"].dropna()

        if not valid_dates.empty:

            print(
                f"Date range: "
                f"{valid_dates.min().date()} "
                f"to "
                f"{valid_dates.max().date()}"
            )

    if "sku" in orders.columns:

        print(
            f"Unique SKUs: "
            f"{orders['sku'].nunique()}"
        )

    print(
        f"Selected elasticity: "
        f"{elasticity:.4f}"
    )

    print(
        f"Selected model: "
        f"{model_name}"
    )

    # --------------------------------------------------------------
    # Baseline
    # --------------------------------------------------------------

    baseline = calculate_baseline(orders)

    print_section(
        "BASELINE COMMERCIAL METRICS"
    )

    print(
        f"Revenue: "
        f"{baseline['revenue']:,.2f}"
    )

    print(
        f"Quantity: "
        f"{baseline['quantity']:,.2f}"
    )

    print(
        f"Weighted average price: "
        f"{baseline['weighted_avg_price']:,.2f}"
    )

    # --------------------------------------------------------------
    # Overall scenarios
    # --------------------------------------------------------------

    scenario_summary = create_scenario_summary(
        orders,
        elasticity,
    )

    print_section(
        "OVERALL PRICING SCENARIOS"
    )

    display_summary = scenario_summary.copy()

    display_summary[
        "price_change_pct"
    ] = display_summary[
        "price_change_pct"
    ].map(lambda x: f"{x:+.0f}%")

    display_summary[
        "quantity_change_pct"
    ] = display_summary[
        "quantity_change_pct"
    ].map(lambda x: f"{x:+.2f}%")

    display_summary[
        "revenue_change_pct"
    ] = display_summary[
        "revenue_change_pct"
    ].map(lambda x: f"{x:+.2f}%")

    display_summary[
        "scenario_revenue"
    ] = display_summary[
        "scenario_revenue"
    ].map(lambda x: f"{x:,.2f}")

    display_summary[
        "revenue_change"
    ] = display_summary[
        "revenue_change"
    ].map(lambda x: f"{x:+,.2f}")

    print(
        display_summary[
            [
                "price_change_pct",
                "quantity_change_pct",
                "revenue_change_pct",
                "scenario_revenue",
                "revenue_change",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------------
    # Business unit
    # --------------------------------------------------------------

    business_unit_summary = (
        create_business_unit_scenarios(
            orders,
            elasticity,
        )
    )

    if not business_unit_summary.empty:

        print_section(
            "BUSINESS UNIT SCENARIOS"
        )

        print(
            business_unit_summary[
                [
                    "business_unit",
                    "price_change_pct",
                    "quantity_change_pct",
                    "revenue_change_pct",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------------
    # Region
    # --------------------------------------------------------------

    region_summary = create_region_scenarios(
        orders,
        elasticity,
    )

    if not region_summary.empty:

        print_section(
            "REGION SCENARIOS"
        )

        print(
            region_summary[
                [
                    "region",
                    "price_change_pct",
                    "revenue_change_pct",
                ]
            ].to_string(index=False)
        )

    # --------------------------------------------------------------
    # SKU
    # --------------------------------------------------------------

    sku_summary = create_sku_scenarios(
        orders,
        elasticity,
    )

    if not sku_summary.empty:

        print_section(
            "SKU SCENARIOS"
        )

        # Focus console output on +5% scenario.
        sku_5 = sku_summary[
            sku_summary["price_change_pct"] == 5
        ].copy()

        sku_5 = sku_5.sort_values(
            "revenue_change",
            ascending=False,
        )

        print(
            sku_5[
                [
                    "sku",
                    "baseline_revenue",
                    "quantity_change_pct",
                    "revenue_change",
                    "revenue_change_pct",
                ]
            ]
            .head(20)
            .to_string(index=False)
        )

    # --------------------------------------------------------------
    # Discount implications
    # --------------------------------------------------------------

    discount_summary = (
        calculate_discount_implications(
            orders,
            elasticity,
        )
    )

    if not discount_summary.empty:

        print_section(
            "DISCOUNT PROFILE"
        )

        print(
            discount_summary.to_string(
                index=False
            )
        )

    # --------------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------------

    overall_file = (
        OUTPUT_DIR
        / "overall_pricing_scenarios.csv"
    )

    business_unit_file = (
        OUTPUT_DIR
        / "business_unit_pricing_scenarios.csv"
    )

    region_file = (
        OUTPUT_DIR
        / "region_pricing_scenarios.csv"
    )

    sku_file = (
        OUTPUT_DIR
        / "sku_pricing_scenarios.csv"
    )

    discount_file = (
        OUTPUT_DIR
        / "discount_profile.csv"
    )

    report_file = (
        OUTPUT_DIR
        / "pricing_scenario_summary.txt"
    )

    scenario_summary.to_csv(
        overall_file,
        index=False,
    )

    if not business_unit_summary.empty:

        business_unit_summary.to_csv(
            business_unit_file,
            index=False,
        )

    if not region_summary.empty:

        region_summary.to_csv(
            region_file,
            index=False,
        )

    if not sku_summary.empty:

        sku_summary.to_csv(
            sku_file,
            index=False,
        )

    if not discount_summary.empty:

        discount_summary.to_csv(
            discount_file,
            index=False,
        )

    report = create_report(
        baseline=baseline,
        elasticity=elasticity,
        p_value=p_value,
        model_name=model_name,
        scenario_summary=scenario_summary,
        business_unit_summary=business_unit_summary,
        robustness_results=robustness_results,
    )

    report_file.write_text(
        report,
        encoding="utf-8",
    )

    # --------------------------------------------------------------
    # Final output
    # --------------------------------------------------------------

    print_section(
        "OUTPUT SAVED"
    )

    print(
        f"Overall scenarios:\n{overall_file}"
    )

    if not business_unit_summary.empty:

        print(
            f"\nBusiness unit scenarios:\n"
            f"{business_unit_file}"
        )

    if not region_summary.empty:

        print(
            f"\nRegion scenarios:\n"
            f"{region_file}"
        )

    if not sku_summary.empty:

        print(
            f"\nSKU scenarios:\n"
            f"{sku_file}"
        )

    if not discount_summary.empty:

        print(
            f"\nDiscount profile:\n"
            f"{discount_file}"
        )

    print(
        f"\nDetailed report:\n{report_file}"
    )

    print()
    print(
        "Pricing scenario analysis complete."
    )


if __name__ == "__main__":
    main()