UPDATE session_ids
       session_expiration = %(session_expiration)s
WHERE
       session_counter = %(session_counter)s;
