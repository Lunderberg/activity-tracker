SELECT
    activity_id,
    activity_name,
    activity_color,
    display
FROM
    activities
WHERE
    user_id = %(user_id)s
