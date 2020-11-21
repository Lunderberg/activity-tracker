WITH temp_summary_windows AS
   (SELECT
       window_seconds,
       datetime('now', CAST(-window_seconds AS TEXT) || ' seconds')
         AS window_start
    FROM
    (
      SELECT 0 as window_seconds
      UNION
      VALUES (:window_seconds)
    ) LIMIT -1 OFFSET 1
   )


SELECT
    window_seconds,
    activity_id,
    -- Need activity_start instead of txn_date, because txn_date might
    -- be before the start of the summary window.
    SUM(JulianDay(activity_end) - JulianDay(activity_start)) * 86400
      AS time_spent_seconds,
    COUNT(*) AS num_periods
FROM
(
    SELECT
       d.*
      ,t.*
      ,MAX(t.txn_date, d.window_start)
       AS activity_start
      ,LEAD(t.txn_date, 1, CURRENT_TIMESTAMP) OVER (
          PARTITION BY t.user_id,d.window_seconds
          ORDER BY t.txn_date ASC
       ) AS activity_end

    FROM temp_summary_windows d
    CROSS JOIN transactions t
    WHERE
         t.user_id = :user_id
    ) inner_query

-- -- Need to filter on activity_end, not txn_date, in order to include
-- -- the period that overlaps with the start of the summary window.
WHERE activity_end > window_start

GROUP BY
     window_seconds, window_start, activity_id
ORDER BY
     window_seconds, window_start, activity_id
;
