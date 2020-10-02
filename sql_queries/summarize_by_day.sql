WITH date_windows AS
(
    SELECT
        date_series AS window_start,
        date_series + interval '1 day' AS window_end
    FROM
        generate_series(
            date_trunc('day', (
                  SELECT MIN(txn_date)
                  FROM transactions
                  WHERE user_id=%(user_id)s
            )),
            CURRENT_DATE,
            interval '1 day') AS date_series
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
         t.user_id = %(user_id)s
)

SELECT
    p.activity_id,
    d.window_start::date AS window_start,
    d.window_end::date AS window_end,
    SUM(LEAST(d.window_end, p.activity_end) - GREATEST(d.window_start,p.txn_date))
    AS time_spent
FROM
    periods p
CROSS JOIN
    date_windows d

WHERE p.txn_date <= d.window_end
  AND p.activity_end >= d.window_start

GROUP BY
     d.window_start, d.window_end, p.activity_id
