import sqlite3

conn = sqlite3.connect("user.db")
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
    security_ans1 TEXT,
);
""")

conn.commit()
conn.close()
