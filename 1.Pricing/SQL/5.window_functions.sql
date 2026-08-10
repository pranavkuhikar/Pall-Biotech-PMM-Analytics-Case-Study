-- ============================================================
-- PART 1: RANKING — Worst discount-offender SKUs per region
-- Window function: RANK() OVER (PARTITION BY ... ORDER BY ...)
-- Business use: flags exactly which SKUs need discount review first,
-- instead of just an average that hides outliers.
-- ============================================================
CREATE OR REPLACE VIEW vw_discount_offenders_ranked AS

WITH sku_discount AS (

    SELECT
        region,
        sku,
        business_unit,
        AVG(discount_pct) AS avg_discount_pct,
        COUNT(*) AS order_count

    FROM orders

    GROUP BY
        region,
        sku,
        business_unit
)

SELECT
    region,
    sku,
    business_unit,
    avg_discount_pct,
    order_count,

    RANK() OVER (
        PARTITION BY region
        ORDER BY avg_discount_pct DESC
    ) AS discount_rank_in_region

FROM sku_discount;


-- Preview
SELECT *
FROM vw_discount_offenders_ranked
WHERE discount_rank_in_region <= 5
ORDER BY region, discount_rank_in_region;



-- ============================================================
-- PART 2: MOVING AVERAGE — Smoothed ASP trend per business unit
-- Window function: AVG() OVER (... ROWS BETWEEN 1 PRECEDING AND CURRENT ROW)
-- Business use: a single quarter's ASP can be noisy (one big deal skews it).
-- A 2-quarter rolling average shows the real trend direction —
-- this is what you'd actually put in front of a VP, not the raw line.
-- ============================================================
CREATE OR REPLACE VIEW vw_asp_moving_avg AS

WITH quarterly_asp AS (

    SELECT
        business_unit,
        DATE_TRUNC('quarter', order_date::date) AS quarter,
        SUM(revenue) / NULLIF(SUM(quantity), 0) AS avg_sell_price

    FROM orders

    GROUP BY
        business_unit,
        DATE_TRUNC('quarter', order_date::date)
)

SELECT
    business_unit,
    quarter,
    avg_sell_price,

    AVG(avg_sell_price) OVER (
        PARTITION BY business_unit
        ORDER BY quarter
        ROWS BETWEEN 1 PRECEDING AND CURRENT ROW
    ) AS asp_2q_moving_avg

FROM quarterly_asp;


SELECT *
FROM vw_asp_moving_avg
ORDER BY business_unit, quarter;


-- ============================================================
-- PART 3: PARETO / CUMULATIVE — Which SKUs drive 80% of revenue
-- Window functions: SUM() OVER (running total) + NTILE() (bucketing)
-- Business use: classic 80/20 check — tells you which handful of SKUs
-- actually matter for pricing governance, so you don't spread
-- discount-review effort evenly across 40 SKUs when 8 of them drive
-- most of the revenue.
-- ============================================================
CREATE OR REPLACE VIEW vw_sku_revenue_pareto AS

WITH sku_revenue AS (

    SELECT
        sku,
        business_unit,
        SUM(revenue) AS total_revenue

    FROM orders

    GROUP BY
        sku,
        business_unit
),

ranked AS (

    SELECT
        sku,
        business_unit,
        total_revenue,

        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_revenue,

        SUM(total_revenue) OVER () AS grand_total_revenue

    FROM sku_revenue
)

SELECT
    sku,
    business_unit,
    total_revenue,

    RANK() OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_rank,

    ROUND(
        (100.0 * running_revenue / grand_total_revenue)::numeric,
        1
    ) AS cumulative_revenue_pct

FROM ranked;


-- Preview
SELECT *
FROM vw_sku_revenue_pareto
ORDER BY revenue_rank;