DROP TABLE IF EXISTS ingredient_index;

CREATE TABLE ingredient_index (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ingredient TEXT NOT NULL,
  product TEXT NOT NULL
);
