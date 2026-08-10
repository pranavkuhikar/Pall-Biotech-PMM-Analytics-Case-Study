CREATE OR REPLACE VIEW vw_discount_creep AS
WITH quarterly_discount AS (
    SELECT
        region,
        DATE_TRUNC('quarter', order_date::date) AS quarter,
        AVG(discount_pct) AS avg_discount
    FROM orders
    GROUP BY region, DATE_TRUNC('quarter', order_date::date)
)
SELECT
    region,
    quarter,
    avg_discount,
    avg_discount - LAG(avg_discount, 4) OVER (PARTITION BY region ORDER BY quarter) AS yoy_discount_change
FROM quarterly_discount
ORDER BY region, quarter;

-- preview it
SELECT * FROM vw_discount_creep WHERE yoy_discount_change IS NOT NULL ORDER BY region, quarter;