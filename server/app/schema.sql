DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS media;

CREATE TABLE players (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  serial TEXT NOT NULL,
  last_ping TEXT,
  on_time TEXT,
  off_time TEXT,
  switch_tab_interval INTEGER
);

CREATE TABLE media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  player_id INTEGER NOT NULL,
  url TEXT NOT NULL,
  FOREIGN KEY (player_id) REFERENCES players (id)
);
