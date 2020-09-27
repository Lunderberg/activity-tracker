INSERT INTO users
       (username, hashed_pw, email_address)
VALUES
       (%(username)s, %(hashed_pw)s, %(email_address)s )
