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

# Drop if exists
cursor.execute("DROP TABLE IF EXISTS collab_lists")
cursor.execute("DROP TABLE IF EXISTS collab_members")
cursor.execute("DROP TABLE IF EXISTS collab_tasks") 

#Collaborative Lists Table
cursor.execute("""
CREATE TABLE collab_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(owner_id) REFERENCES users(id)
);
""") 

#Collaborative Members Table
cursor.execute("""
CREATE TABLE collab_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    user_email TEXT NOT NULL,
    added_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(list_id) REFERENCES collab_lists(id)
);
""")

#Collaborative Tasks Table
cursor.execute("""
CREATE TABLE collab_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'ongoing', 'done')) DEFAULT 'pending',
    priority TEXT CHECK(priority IN ('important','mid','easy')) DEFAULT 'easy',
    deadline TEXT,
    duetime TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(list_id) REFERENCES collab_lists(id)
);
""")

conn.commit()
conn.close()
