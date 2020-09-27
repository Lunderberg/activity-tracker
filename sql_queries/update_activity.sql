INSERT INTO activities
    (user_id, activity_id,
     activity_name, activity_color,
     display)
VALUES
    (%(user_id)s, %(activity_id)s,
    %(activity_name)s, %(activity_color)s,
     %(display)s)

ON CONFLICT (user_id,activity_id) DO UPDATE SET
    activity_name = excluded.activity_name,
    activity_color = excluded.activity_color,
    display = excluded.display
