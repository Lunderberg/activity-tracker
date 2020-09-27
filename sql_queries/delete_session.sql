DELETE FROM
        session_ids s
WHERE
        s.session_counter = %(session_counter)s;
