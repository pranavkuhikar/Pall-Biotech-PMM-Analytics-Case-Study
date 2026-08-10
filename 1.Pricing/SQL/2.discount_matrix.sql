CREATE OR REPLACE VIEW vw_discount_matrix AS
SELECT
    channel,
    customer_tier,
    region,
    ROUND(AVG(discount_pct)::numeric, 2)    AS avg_discount_pct,
    ROUND(STDDEV(discount_pct)::numeric, 2) AS discount_variance,
    COUNT(*)                                 AS order_count
FROM orders
GROUP BY channel, customer_tier, region
ORDER BY avg_discount_pct DESC;

-- preview it
SELECT * FROM vw_discount_matrix;