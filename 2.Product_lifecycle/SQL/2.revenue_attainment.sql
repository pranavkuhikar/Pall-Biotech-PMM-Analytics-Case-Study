DROP VIEW IF EXISTS vw_revenue_attainment;

CREATE VIEW vw_revenue_attainment AS

SELECT

    initiative_id,

    initiative_name,

    business_unit,

    region,

    quarter,

    planned_revenue,

    actual_revenue,

    ROUND((actual_revenue-planned_revenue)::numeric,2) AS revenue_variance,

    ROUND(
        ((actual_revenue/planned_revenue)*100)::numeric,
        2
    ) AS revenue_attainment_pct,

    status,

    risk_category

FROM initiatives_scored

ORDER BY

    revenue_attainment_pct DESC;