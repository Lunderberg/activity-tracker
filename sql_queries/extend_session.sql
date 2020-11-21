UPDATE session_ids
SET
       session_expiration = :session_expiration
WHERE
       rowid = :session_counter;
