DROP VIEW IF EXISTS vw_price_vs_index;

CREATE OR REPLACE VIEW vw_price_vs_index AS

WITH quarterly_ppi AS (
    SELECT
        DATE_TRUNC('quarter', observation_date::date) AS quarter,
        AVG("PCU325211325211"::numeric) AS ppi_index
    FROM raw_material_index
    GROUP BY DATE_TRUNC('quarter', observation_date::date)
)

SELECT
    o.business_unit,
    DATE_TRUNC('quarter', o.order_date::date) AS quarter,
    ROUND(AVG(o.list_price), 2) AS avg_list_price,
    ROUND(ppi.ppi_index, 2) AS ppi_index
FROM orders o

JOIN quarterly_ppi ppi
    ON DATE_TRUNC('quarter', o.order_date::date) = ppi.quarter

GROUP BY
    o.business_unit,
    DATE_TRUNC('quarter', o.order_date::date),
    ppi.ppi_index

ORDER BY
    o.business_unit,
    quarter;


SELECT *
FROM vw_price_vs_index
ORDER BY business_unit, quarter;