SELECT
     txn_date
    ,activity_id
FROM
     transactions
WHERE
     user_id = :user_id
 AND txn_date > :min_time
 AND txn_date < :max_time
