DROP VIEW IF EXISTS vw_otd_analysis;

CREATE VIEW vw_otd_analysis AS

SELECT

    business_unit,

    region,

    quarter,

    ROUND(AVG(planned_otd_pct)::numeric,2) AS planned_otd,

    ROUND(AVG(actual_otd_pct)::numeric,2) AS actual_otd,

    ROUND(
        AVG(actual_otd_pct-planned_otd_pct)::numeric,
        2
    ) AS otd_variance,

    ROUND(AVG(backlog_days)::numeric,2) AS avg_backlog,

    SUM(
        CASE
            WHEN actual_otd_pct>=95
            THEN 1
            ELSE 0
        END
    ) AS on_time_initiatives,

    COUNT(*) AS total_records

FROM initiatives_scored

GROUP BY

    business_unit,
    region,
    quarter

ORDER BY

    quarter,
    business_unit;