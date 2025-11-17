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

cursor.execute("DROP TABLE IF EXISTS tasks")

cursor.execute("""
CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    deadline TEXT,
    duetime TEXT,
    status TEXT CHECK(status IN ('pending', 'ongoing', 'done')) DEFAULT 'pending',
    priority TEXT CHECK(priority IN ('important','mid','easy')) DEFAULT 'easy',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(owner_id) REFERENCES users(id)
);
""")

cursor.execute("DROP TABLE IF EXISTS task_collaborators")

cursor.execute("""
CREATE TABLE task_collaborators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT CHECK(role IN ('owner','editor','viewer')) NOT NULL DEFAULT 'viewer',
    added_at TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(task_id, user_id),
    FOREIGN KEY(task_id) REFERENCES tasks(task_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

conn.commit()
conn.close()
