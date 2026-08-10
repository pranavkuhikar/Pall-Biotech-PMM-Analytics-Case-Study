DROP VIEW IF EXISTS vw_aos_summary;

CREATE VIEW vw_aos_summary AS

SELECT

    business_unit,

    region,

    COUNT(DISTINCT initiative_id) AS initiatives,

    COUNT(*) AS observations,

    ROUND(AVG(aos_health)::numeric,3) AS avg_aos,

    ROUND((AVG(revenue_attainment)*100)::numeric,2) AS revenue_attainment_pct,

    ROUND(AVG(actual_otd_pct)::numeric,2) AS avg_otd_pct,

    ROUND(AVG(backlog_days)::numeric,2) AS avg_backlog_days,

    ROUND(SUM(actual_revenue)::numeric,2) AS total_revenue,

    SUM(CASE WHEN status='Green' THEN 1 ELSE 0 END) AS green_count,

    SUM(CASE WHEN status='Amber' THEN 1 ELSE 0 END) AS amber_count,

    SUM(CASE WHEN status='Red' THEN 1 ELSE 0 END) AS red_count

FROM initiatives_scored

GROUP BY

    business_unit,
    region

ORDER BY

    avg_aos DESC;