SELECT
     txn_date
    ,activity_id
FROM
     transactions
WHERE
     user_id = %(user_id)s
 AND txn_date > %(min_time)s
 AND txn_date < %(max_time)s
