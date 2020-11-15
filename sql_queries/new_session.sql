INSERT INTO session_ids
       (user_id, hashed_session_id, session_expiration)
VALUES
       (:user_id, :hashed_session_id, :session_expiration )
