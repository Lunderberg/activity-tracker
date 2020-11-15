DELETE FROM
       transactions
WHERE
       user_id = :user_id
   AND txn_date >= :window_start
   AND txn_date <= :window_end
