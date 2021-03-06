CREATE TABLE IF NOT EXISTS users (
  user_id UUID NOT NULL UNIQUE,
  username TEXT NOT NULL UNIQUE,
  hashed_pw TEXT NOT NULL,
  email_address TEXT,

  PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS session_ids (
  user_id UUID REFERENCES users(user_id),
  hashed_session_id TEXT NOT NULL,
  session_expiration TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
  user_id UUID,
  txn_date TIMESTAMP WITH TIME ZONE,
  activity_id INTEGER NOT NULL,

  PRIMARY KEY (user_id, txn_date)
);

CREATE TABLE IF NOT EXISTS activities (
  user_id UUID,
  activity_id INTEGER,
  activity_name TEXT,
  activity_color TEXT,
  display BOOLEAN,

  PRIMARY KEY (user_id, activity_id)
);
