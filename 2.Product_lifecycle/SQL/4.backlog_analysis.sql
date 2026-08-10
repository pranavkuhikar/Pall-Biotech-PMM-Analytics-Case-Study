DROP VIEW IF EXISTS vw_backlog_analysis;

CREATE VIEW vw_backlog_analysis AS

SELECT

    initiative_id,

    initiative_name,

    business_unit,

    region,

    quarter,

    backlog_days,

    status,

    risk_category,

    ROW_NUMBER()

    OVER
    (
        PARTITION BY region
        ORDER BY backlog_days DESC
    )

    AS backlog_rank

FROM initiatives_scored

ORDER BY

    backlog_days DESC;