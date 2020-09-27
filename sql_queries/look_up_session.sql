SELECT
        s.*,
        (CURRENT_TIMESTAMP < s.session_expiration) AS session_active
FROM
        session_ids s
WHERE
        s.session_counter = %(session_counter)s
    AND s.user_id = %(user_id)s
