SELECT
        s.*,
        (CURRENT_TIMESTAMP < s.session_expiration) AS session_active
FROM
        session_ids s
WHERE
        s.rowid = :session_counter
    AND s.user_id = :user_id
