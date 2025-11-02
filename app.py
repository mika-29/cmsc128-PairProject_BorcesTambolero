import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# If table exists, drop it
cursor.execute("DROP TABLE IF EXISTS users")

# Create new table
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    security_q1 TEXT,
    security_ans1 TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    deadline TEXT,
    duetime TEXT,
    status TEXT CHECK(status IN ('pending', 'ongoing', 'done')) DEFAULT 'pending',
    priority TEXT CHECK(priority IN ('important','mid','easy')) DEFAULT 'easy',
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
""")

conn.commit()
conn.close()
