CREATE OR REPLACE VIEW vw_price_realization AS
SELECT
    business_unit,
    region,
    channel,
    customer_tier,
    DATE_TRUNC('quarter', order_date::date) AS quarter,
    SUM(revenue) / NULLIF(SUM(quantity), 0)   AS avg_sell_price,
    AVG(list_price)                            AS avg_list_price,
    AVG(discount_pct)                          AS avg_discount_pct,
    SUM(revenue)                               AS total_revenue,
    SUM(quantity)                              AS total_units
FROM orders
GROUP BY business_unit, region, channel, customer_tier, DATE_TRUNC('quarter', order_date::date);

-- preview it
SELECT * FROM vw_price_realization ORDER BY quarter, business_unit LIMIT 50;