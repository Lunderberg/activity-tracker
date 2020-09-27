INSERT INTO session_ids
       (user_id, hashed_session_id, session_expiration)
VALUES
       (%(user_id)s, %(hashed_session_id)s, %(session_expiration)s )
RETURNING
       session_counter
