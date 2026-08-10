"""
Pall Biotech PMM Analytics
Pricing Scenario Simulator

Purpose
-------
Translate the validated price elasticity estimate into practical
pricing scenarios.

The model estimates the expected impact of alternative net-price
increases on:

    1. Quantity
    2. Revenue
    3. Revenue uplift
    4. Volume loss
    5. Implied discount
    6. Price realization
    7. SKU / segment opportunity

Validated elasticity:
    -0.6920

This is an observational elasticity estimate. Scenario results
should therefore be interpreted as estimated commercial scenarios,
not guaranteed causal outcomes.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ELASTICITY = -0.6920

# Robustness estimates from robustness_analysis.py
ELASTICITY_LOW = -0.5822
ELASTICITY_HIGH = -0.7886

# Price scenarios
PRICE_SCENARIOS = [0.00, 0.02, 0.05, 0.10, 0.15]

# Minimum revenue threshold for identifying meaningful SKU
# opportunities.
MIN_REVENUE = 100_000

# Minimum revenue uplift required for an opportunity.
MIN_REVENUE_UPLIFT = 0

# Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Data"
OUTPUT_DIR = BASE_DIR / "pricing_scenarios"

ORDERS_FILE = DATA_DIR / "orders.csv"

# Output files
SCENARIO_FILE = OUTPUT_DIR / "pricing_scenarios.csv"
SKU_FILE = OUTPUT_DIR / "sku_pricing_opportunities.csv"
SEGMENT_FILE = OUTPUT_DIR / "segment_pricing_opportunities.csv"
SENSITIVITY_FILE = OUTPUT_DIR / "elasticity_sensitivity.csv"
SUMMARY_FILE = OUTPUT_DIR / "pricing_scenario_summary.txt"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    """Print a formatted console section."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def validate_columns(df):
    """Validate that the orders file contains required columns."""

    required_columns = [
        "order_id",
        "order_date",
        "business_unit",
        "sku",
        "region",
        "channel",
        "customer_tier",
        "list_price",
        "net_price",
        "discount_pct",
        "quantity",
        "revenue",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Orders file is missing required columns: "
            + ", ".join(missing)
        )


def load_orders():
    """Load and validate order data."""

    print(f"Loading orders from:\n{ORDERS_FILE}")

    if not ORDERS_FILE.exists():
        raise FileNotFoundError(
            f"Orders file not found:\n{ORDERS_FILE}"
        )

    orders = pd.read_csv(ORDERS_FILE)

    validate_columns(orders)

    # Parse date
    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    # Convert numerical columns
    numeric_columns = [
        "list_price",
        "net_price",
        "discount_pct",
        "quantity",
        "revenue",
    ]

    for column in numeric_columns:
        orders[column] = pd.to_numeric(
            orders[column],
            errors="coerce"
        )

    # Remove unusable observations
    before = len(orders)

    orders = orders.dropna(
        subset=[
            "order_date",
            "sku",
            "list_price",
            "net_price",
            "quantity",
        ]
    )

    orders = orders[
        (orders["net_price"] > 0)
        & (orders["list_price"] > 0)
        & (orders["quantity"] > 0)
    ].copy()

    removed = before - len(orders)

    if removed > 0:
        print(f"Removed invalid rows: {removed}")

    if orders.empty:
        raise ValueError("No valid orders remain after cleaning.")

    return orders


def calculate_elastic_quantity_factor(
    price_change,
    elasticity
):
    """
    Calculate quantity response using constant elasticity.

    Q1 / Q0 = (P1 / P0)^elasticity

    Therefore:

    quantity_factor =
        (1 + price_change) ^ elasticity
    """

    return (1 + price_change) ** elasticity


def add_scenario_metrics(
    orders,
    price_change,
    elasticity
):
    """
    Apply a price scenario at order level.

    This preserves the actual mix of SKUs, regions, customers,
    quantities and prices.
    """

    result = orders.copy()

    price_factor = 1 + price_change

    quantity_factor = calculate_elastic_quantity_factor(
        price_change,
        elasticity
    )

    result["scenario_price_change"] = price_change

    result["scenario_elasticity"] = elasticity

    # New net price
    result["scenario_net_price"] = (
        result["net_price"] * price_factor
    )

    # Expected quantity
    result["baseline_quantity"] = result["quantity"]

    result["scenario_quantity"] = (
        result["quantity"] * quantity_factor
    )

    # Expected revenue
    result["baseline_revenue"] = (
        result["net_price"] * result["quantity"]
    )

    result["scenario_revenue"] = (
        result["scenario_net_price"]
        * result["scenario_quantity"]
    )

    # Absolute changes
    result["quantity_change"] = (
        result["scenario_quantity"]
        - result["baseline_quantity"]
    )

    result["revenue_change"] = (
        result["scenario_revenue"]
        - result["baseline_revenue"]
    )

    # Percentage changes
    result["quantity_change_pct"] = (
        result["scenario_quantity"]
        / result["baseline_quantity"]
        - 1
    ) * 100

    result["revenue_change_pct"] = (
        result["scenario_revenue"]
        / result["baseline_revenue"]
        - 1
    ) * 100

    # Implied discount after price increase
    result["scenario_discount_pct"] = (
        1
        - result["scenario_net_price"]
        / result["list_price"]
    ) * 100

    # Price realization
    result["baseline_price_realization_pct"] = (
        result["net_price"]
        / result["list_price"]
    ) * 100

    result["scenario_price_realization_pct"] = (
        result["scenario_net_price"]
        / result["list_price"]
    ) * 100

    # Flag cases where the scenario exceeds list price.
    result["above_list_price"] = (
        result["scenario_net_price"]
        > result["list_price"]
    )

    return result


def aggregate_scenario(result):
    """Aggregate scenario results."""

    baseline_revenue = result["baseline_revenue"].sum()
    scenario_revenue = result["scenario_revenue"].sum()

    baseline_quantity = result["baseline_quantity"].sum()
    scenario_quantity = result["scenario_quantity"].sum()

    baseline_price = (
        result["baseline_revenue"].sum()
        / result["baseline_quantity"].sum()
    )

    scenario_price = (
        result["scenario_revenue"].sum()
        / result["scenario_quantity"].sum()
    )

    return {
        "elasticity": result["scenario_elasticity"].iloc[0],
        "price_increase_pct": (
            result["scenario_price_change"].iloc[0] * 100
        ),
        "orders": len(result),
        "baseline_quantity": baseline_quantity,
        "scenario_quantity": scenario_quantity,
        "quantity_change": (
            scenario_quantity - baseline_quantity
        ),
        "quantity_change_pct": (
            scenario_quantity / baseline_quantity - 1
        ) * 100,
        "baseline_revenue": baseline_revenue,
        "scenario_revenue": scenario_revenue,
        "revenue_change": (
            scenario_revenue - baseline_revenue
        ),
        "revenue_change_pct": (
            scenario_revenue / baseline_revenue - 1
        ) * 100,
        "baseline_avg_net_price": baseline_price,
        "scenario_avg_net_price": scenario_price,
        "orders_above_list_price": int(
            result["above_list_price"].sum()
        ),
        "pct_orders_above_list_price": (
            result["above_list_price"].mean() * 100
        ),
    }


def build_scenario_table(orders):
    """Build overall pricing scenario table."""

    rows = []

    for price_change in PRICE_SCENARIOS:

        scenario = add_scenario_metrics(
            orders,
            price_change,
            ELASTICITY
        )

        rows.append(
            aggregate_scenario(scenario)
        )

    return pd.DataFrame(rows)


def build_sku_opportunities(orders):
    """
    Calculate pricing scenarios at SKU level.

    The 5% price increase is used as the primary opportunity
    scenario because it represents a relatively moderate
    commercial intervention.
    """

    scenario = add_scenario_metrics(
        orders,
        0.05,
        ELASTICITY
    )

    grouped = (
        scenario
        .groupby(
            [
                "sku",
                "business_unit",
            ],
            as_index=False
        )
        .agg(
            baseline_revenue=(
                "baseline_revenue",
                "sum"
            ),
            scenario_revenue=(
                "scenario_revenue",
                "sum"
            ),
            baseline_quantity=(
                "baseline_quantity",
                "sum"
            ),
            scenario_quantity=(
                "scenario_quantity",
                "sum"
            ),
            avg_list_price=(
                "list_price",
                "mean"
            ),
            avg_net_price=(
                "net_price",
                "mean"
            ),
            avg_discount_pct=(
                "discount_pct",
                "mean"
            ),
            avg_scenario_discount_pct=(
                "scenario_discount_pct",
                "mean"
            ),
            orders=(
                "order_id",
                "count"
            ),
            orders_above_list_price=(
                "above_list_price",
                "sum"
            ),
        )
    )

    grouped["revenue_change"] = (
        grouped["scenario_revenue"]
        - grouped["baseline_revenue"]
    )

    grouped["revenue_change_pct"] = (
        grouped["scenario_revenue"]
        / grouped["baseline_revenue"]
        - 1
    ) * 100

    grouped["quantity_change"] = (
        grouped["scenario_quantity"]
        - grouped["baseline_quantity"]
    )

    grouped["quantity_change_pct"] = (
        grouped["scenario_quantity"]
        / grouped["baseline_quantity"]
        - 1
    ) * 100

    grouped["price_increase_pct"] = 5.0

    grouped["elasticity"] = ELASTICITY

    grouped["pct_orders_above_list_price"] = (
        grouped["orders_above_list_price"]
        / grouped["orders"]
    ) * 100

    # Commercial opportunity flag
    grouped["opportunity"] = np.where(
        (
            (grouped["baseline_revenue"] >= MIN_REVENUE)
            & (grouped["revenue_change"] > MIN_REVENUE_UPLIFT)
            & (grouped["pct_orders_above_list_price"] == 0)
        ),
        "Potential price increase",
        "Review"
    )

    # Rank by revenue opportunity
    grouped["opportunity_rank"] = (
        grouped["revenue_change"]
        .rank(
            ascending=False,
            method="dense"
        )
        .astype(int)
    )

    grouped = grouped.sort_values(
        "revenue_change",
        ascending=False
    )

    return grouped


def build_segment_opportunities(orders):
    """
    Calculate the 5% scenario across commercial segments.
    """

    scenario = add_scenario_metrics(
        orders,
        0.05,
        ELASTICITY
    )

    grouped = (
        scenario
        .groupby(
            [
                "business_unit",
                "region",
                "channel",
                "customer_tier",
            ],
            as_index=False
        )
        .agg(
            baseline_revenue=(
                "baseline_revenue",
                "sum"
            ),
            scenario_revenue=(
                "scenario_revenue",
                "sum"
            ),
            baseline_quantity=(
                "baseline_quantity",
                "sum"
            ),
            scenario_quantity=(
                "scenario_quantity",
                "sum"
            ),
            orders=(
                "order_id",
                "count"
            ),
            avg_net_price=(
                "net_price",
                "mean"
            ),
            avg_discount_pct=(
                "discount_pct",
                "mean"
            ),
            avg_scenario_discount_pct=(
                "scenario_discount_pct",
                "mean"
            ),
            orders_above_list_price=(
                "above_list_price",
                "sum"
            ),
        )
    )

    grouped["revenue_change"] = (
        grouped["scenario_revenue"]
        - grouped["baseline_revenue"]
    )

    grouped["revenue_change_pct"] = (
        grouped["scenario_revenue"]
        / grouped["baseline_revenue"]
        - 1
    ) * 100

    grouped["quantity_change"] = (
        grouped["scenario_quantity"]
        - grouped["baseline_quantity"]
    )

    grouped["quantity_change_pct"] = (
        grouped["scenario_quantity"]
        / grouped["baseline_quantity"]
        - 1
    ) * 100

    grouped["price_increase_pct"] = 5.0

    grouped["pct_orders_above_list_price"] = (
        grouped["orders_above_list_price"]
        / grouped["orders"]
    ) * 100

    grouped = grouped.sort_values(
        "revenue_change",
        ascending=False
    )

    return grouped


def build_elasticity_sensitivity(orders):
    """
    Test the commercial impact of the 5% price scenario under
    multiple elasticity assumptions.

    This demonstrates how sensitive the revenue recommendation
    is to the estimated elasticity.
    """

    elasticity_values = [
        ELASTICITY_LOW,
        ELASTICITY,
        ELASTICITY_HIGH,
    ]

    labels = [
        "Less elastic / conservative",
        "Validated base case",
        "More elastic / downside",
    ]

    rows = []

    for elasticity, label in zip(
        elasticity_values,
        labels
    ):

        scenario = add_scenario_metrics(
            orders,
            0.05,
            elasticity
        )

        result = aggregate_scenario(scenario)

        result["case"] = label

        rows.append(result)

    return pd.DataFrame(rows)


def create_summary(
    orders,
    scenario_table,
    sku_opportunities,
    segment_opportunities,
    sensitivity
):
    """Create a human-readable summary."""

    baseline = scenario_table.iloc[0]
    five_pct = scenario_table[
        scenario_table["price_increase_pct"] == 5.0
    ].iloc[0]

    ten_pct = scenario_table[
        scenario_table["price_increase_pct"] == 10.0
    ].iloc[0]

    fifteen_pct = scenario_table[
        scenario_table["price_increase_pct"] == 15.0
    ].iloc[0]

    top_skus = sku_opportunities.head(10)

    total_baseline_revenue = baseline["baseline_revenue"]

    lines = []

    lines.append(
        "PALL BIOTECH PMM ANALYTICS"
    )
    lines.append(
        "PRICING SCENARIO ANALYSIS"
    )
    lines.append("=" * 70)
    lines.append("")

    lines.append(
        "MODEL BASIS"
    )
    lines.append("-" * 70)
    lines.append(
        f"Orders used: {len(orders):,}"
    )
    lines.append(
        f"Validated elasticity: {ELASTICITY:.4f}"
    )
    lines.append(
        f"Elasticity sensitivity range: "
        f"{ELASTICITY_LOW:.4f} to {ELASTICITY_HIGH:.4f}"
    )
    lines.append(
        f"Date range: "
        f"{orders['order_date'].min().date()} to "
        f"{orders['order_date'].max().date()}"
    )
    lines.append(
        f"Baseline revenue: "
        f"${total_baseline_revenue:,.2f}"
    )
    lines.append("")

    lines.append(
        "OVERALL PRICING SCENARIOS"
    )
    lines.append("-" * 70)

    for _, row in scenario_table.iterrows():

        lines.append(
            f"{row['price_increase_pct']:>5.1f}% price increase | "
            f"Quantity: {row['quantity_change_pct']:>7.2f}% | "
            f"Revenue: {row['revenue_change_pct']:>7.2f}% | "
            f"Revenue change: "
            f"${row['revenue_change']:>14,.2f}"
        )

    lines.append("")

    lines.append(
        "PRIMARY 5% SCENARIO"
    )
    lines.append("-" * 70)

    lines.append(
        f"Expected quantity change: "
        f"{five_pct['quantity_change_pct']:.2f}%"
    )

    lines.append(
        f"Expected revenue change: "
        f"{five_pct['revenue_change_pct']:.2f}%"
    )

    lines.append(
        f"Expected revenue uplift: "
        f"${five_pct['revenue_change']:,.2f}"
    )

    lines.append(
        f"Orders above list price: "
        f"{five_pct['orders_above_list_price']:,} "
        f"({five_pct['pct_orders_above_list_price']:.2f}%)"
    )

    lines.append("")

    lines.append(
        "HIGHER PRICE SCENARIOS"
    )
    lines.append("-" * 70)

    lines.append(
        f"10% increase: "
        f"{ten_pct['revenue_change_pct']:.2f}% revenue change "
        f"(${ten_pct['revenue_change']:,.2f})"
    )

    lines.append(
        f"15% increase: "
        f"{fifteen_pct['revenue_change_pct']:.2f}% revenue change "
        f"(${fifteen_pct['revenue_change']:,.2f})"
    )

    lines.append("")

    lines.append(
        "TOP SKU OPPORTUNITIES"
    )
    lines.append("-" * 70)

    for _, row in top_skus.iterrows():

        lines.append(
            f"{row['sku']:>8} | "
            f"{row['business_unit']:<25} | "
            f"Revenue uplift: "
            f"${row['revenue_change']:>12,.2f} | "
            f"{row['revenue_change_pct']:>6.2f}% | "
            f"{row['opportunity']}"
        )

    lines.append("")

    lines.append(
        "ELASTICITY SENSITIVITY"
    )
    lines.append("-" * 70)

    for _, row in sensitivity.iterrows():

        lines.append(
            f"{row['case']:<32} | "
            f"Elasticity: {row['elasticity']:.4f} | "
            f"Revenue change: "
            f"{row['revenue_change_pct']:.2f}% | "
            f"Revenue uplift: "
            f"${row['revenue_change']:,.2f}"
        )

    lines.append("")

    lines.append(
        "ECONOMETRIC AND COMMERCIAL LIMITATIONS"
    )
    lines.append("-" * 70)

    lines.append(
        "1. The elasticity estimate comes from observational pricing data."
    )

    lines.append(
        "2. Scenario results are estimated associations, not guaranteed "
        "causal outcomes."
    )

    lines.append(
        "3. The model assumes the estimated elasticity remains stable "
        "under the scenario."
    )

    lines.append(
        "4. The model does not explicitly model competitor pricing, "
        "capacity constraints, contract renegotiation, or customer churn."
    )

    lines.append(
        "5. Price increases that push net price above list price should "
        "be reviewed before implementation."
    )

    lines.append(
        "6. SKU-level recommendations should be validated with commercial "
        "teams before execution."
    )

    lines.append("")

    lines.append(
        "RECOMMENDED USE"
    )
    lines.append("-" * 70)

    lines.append(
        "Use the 5% scenario as the initial commercial planning case."
    )

    lines.append(
        "Prioritise high-revenue SKUs and segments where the scenario "
        "produces positive revenue uplift without exceeding list price."
    )

    lines.append(
        "Treat the elasticity sensitivity analysis as a risk range rather "
        "than a forecast guarantee."
    )

    lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():

    print_section(
        "PALL BIOTECH PMM - PRICING SCENARIO ANALYSIS"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    orders = load_orders()

    print()
    print(f"Orders loaded: {len(orders):,}")
    print(
        f"Date range: "
        f"{orders['order_date'].min().date()} to "
        f"{orders['order_date'].max().date()}"
    )

    print(
        f"Baseline revenue: "
        f"${(orders['net_price'] * orders['quantity']).sum():,.2f}"
    )

    print(
        f"Unique SKUs: "
        f"{orders['sku'].nunique():,}"
    )

    print(
        f"Unique business units: "
        f"{orders['business_unit'].nunique():,}"
    )

    print(
        f"Unique regions: "
        f"{orders['region'].nunique():,}"
    )

    # --------------------------------------------------------
    # Overall scenarios
    # --------------------------------------------------------

    print_section(
        "OVERALL PRICING SCENARIOS"
    )

    scenario_table = build_scenario_table(
        orders
    )

    print(
        scenario_table[
            [
                "price_increase_pct",
                "quantity_change_pct",
                "revenue_change_pct",
                "revenue_change",
                "orders_above_list_price",
                "pct_orders_above_list_price",
            ]
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # SKU opportunities
    # --------------------------------------------------------

    print_section(
        "TOP SKU PRICING OPPORTUNITIES"
    )

    sku_opportunities = build_sku_opportunities(
        orders
    )

    display_columns = [
        "sku",
        "business_unit",
        "baseline_revenue",
        "revenue_change",
        "revenue_change_pct",
        "quantity_change_pct",
        "avg_discount_pct",
        "avg_scenario_discount_pct",
        "pct_orders_above_list_price",
        "opportunity",
    ]

    print(
        sku_opportunities[
            display_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Segment opportunities
    # --------------------------------------------------------

    print_section(
        "TOP COMMERCIAL SEGMENT OPPORTUNITIES"
    )

    segment_opportunities = (
        build_segment_opportunities(
            orders
        )
    )

    segment_columns = [
        "business_unit",
        "region",
        "channel",
        "customer_tier",
        "baseline_revenue",
        "revenue_change",
        "revenue_change_pct",
        "quantity_change_pct",
        "avg_discount_pct",
        "avg_scenario_discount_pct",
        "pct_orders_above_list_price",
    ]

    print(
        segment_opportunities[
            segment_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Sensitivity
    # --------------------------------------------------------

    print_section(
        "ELASTICITY SENSITIVITY"
    )

    sensitivity = build_elasticity_sensitivity(
        orders
    )

    print(
        sensitivity[
            [
                "case",
                "elasticity",
                "price_increase_pct",
                "quantity_change_pct",
                "revenue_change_pct",
                "revenue_change",
            ]
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------

    scenario_table.to_csv(
        SCENARIO_FILE,
        index=False
    )

    sku_opportunities.to_csv(
        SKU_FILE,
        index=False
    )

    segment_opportunities.to_csv(
        SEGMENT_FILE,
        index=False
    )

    sensitivity.to_csv(
        SENSITIVITY_FILE,
        index=False
    )

    summary = create_summary(
        orders,
        scenario_table,
        sku_opportunities,
        segment_opportunities,
        sensitivity,
    )

    SUMMARY_FILE.write_text(
        summary,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print_section(
        "OUTPUTS SAVED"
    )

    print(
        f"Overall scenarios:\n{SCENARIO_FILE}"
    )

    print(
        f"\nSKU opportunities:\n{SKU_FILE}"
    )

    print(
        f"\nSegment opportunities:\n{SEGMENT_FILE}"
    )

    print(
        f"\nElasticity sensitivity:\n{SENSITIVITY_FILE}"
    )

    print(
        f"\nSummary:\n{SUMMARY_FILE}"
    )

    print()
    print(
        "Pricing scenario analysis complete."
    )


if __name__ == "__main__":
    main()