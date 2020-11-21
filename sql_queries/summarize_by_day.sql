WITH
RECURSIVE date_windows(window_start, window_end) AS
(
   SELECT
        date(MIN(txn_date)),
        date(date(MIN(txn_date)), '+1 day')
   FROM transactions WHERE user_id=:user_id

   UNION ALL
   SELECT
        window_end,
        date(window_end, '+1 day')
   FROM date_windows
   WHERE window_start < CURRENT_DATE
),

periods AS
(SELECT
       t.*
      ,LEAD(t.txn_date, 1, CURRENT_TIMESTAMP) OVER (
          PARTITION BY t.user_id
          ORDER BY t.txn_date ASC
       ) AS activity_end
    FROM transactions t
    WHERE
         t.user_id = :user_id
)


SELECT
     p.activity_id,
     d.window_start,
     d.window_end,
     SUM(MIN(JulianDay(d.window_end), JulianDay(p.activity_end)) -
         MAX(JulianDay(d.window_start), JulianDay(p.txn_date))) * 86400
     AS time_spent_seconds
FROM
     periods p
CROSS JOIN
     date_windows d

WHERE p.txn_date <= d.window_end
  AND p.activity_end >= d.window_start

GROUP BY
     d.window_start, d.window_end, p.activity_id
ORDER BY
     d.window_start, d.window_end, p.activity_id
