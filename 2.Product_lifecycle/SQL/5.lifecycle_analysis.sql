DROP VIEW IF EXISTS vw_lifecycle_analysis;

CREATE VIEW vw_lifecycle_analysis AS

SELECT

    lifecycle_stage,

    business_unit,

    COUNT(DISTINCT initiative_id) AS initiatives,

    ROUND(AVG(aos_health)::numeric,3) AS avg_aos,

    ROUND((AVG(revenue_attainment)*100)::numeric,2) AS revenue_attainment_pct,

    ROUND(AVG(actual_otd_pct)::numeric,2) AS avg_otd,

    ROUND(AVG(backlog_days)::numeric,2) AS avg_backlog,

    ROUND(AVG(customer_adoption_pct)::numeric,2) AS avg_adoption,

    ROUND(AVG(gross_margin_pct)::numeric,2) AS avg_margin,

    ROUND(SUM(actual_revenue)::numeric,2) AS total_revenue

FROM initiatives_scored

GROUP BY

    lifecycle_stage,
    business_unit

ORDER BY

    avg_aos DESC;