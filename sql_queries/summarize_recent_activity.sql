DROP TABLE IF EXISTS temp_summary_windows;

CREATE TEMPORARY TABLE temp_summary_windows (
  summary_window INTERVAL
);

INSERT INTO temp_summary_windows
  (summary_window)
VALUES
  (%(summary_window)s);


SELECT
    summary_window,
    activity_id,
    -- Need activity_start, because txn_date might be before the start
    -- of the summary window.
    SUM(activity_end - activity_start) AS time_spent,
    COUNT(*) AS num_periods
FROM
(
    SELECT
       d.*
      ,t.*
      ,GREATEST(t.txn_date, CURRENT_TIMESTAMP - d.summary_window)
       AS activity_start
      ,LEAD(t.txn_date, 1, CURRENT_TIMESTAMP) OVER (
          PARTITION BY t.user_id,d.summary_window
          ORDER BY t.txn_date ASC
       ) AS activity_end
    FROM temp_summary_windows d
    CROSS JOIN transactions t
    WHERE
         t.user_id = %(user_id)s
) inner_query

-- Need to filter on activity_end, not txn_date, in order to include
-- the period that overlaps with the start of the summary window.
WHERE activity_end > CURRENT_TIMESTAMP - summary_window

GROUP BY
     summary_window, activity_id
ORDER BY
     summary_window, activity_id
;
