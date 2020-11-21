DELETE FROM
       session_ids
WHERE
       session_expiration < CURRENT_TIMESTAMP;
