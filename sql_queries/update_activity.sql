INSERT OR REPLACE INTO activities
    (user_id, activity_id,
     activity_name, activity_color,
     display)
VALUES
    (:user_id, :activity_id,
    :activity_name, :activity_color,
     :display);
