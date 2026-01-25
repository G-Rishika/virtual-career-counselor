CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT
);

CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY,
    career_goal TEXT,
    current_level TEXT,
    interests TEXT,
    time_per_week INTEGER
);

CREATE TABLE roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    roadmap TEXT,
    created_at TEXT
);
