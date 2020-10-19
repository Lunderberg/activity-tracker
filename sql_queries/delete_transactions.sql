DELETE FROM
       transactions
WHERE
       user_id = %(user_id)s
   AND txn_date >= %(window_start)s
   AND txn_date <= %(window_end)s
