import sqlite3

conn = sqlite3.connect("todo.db")   #manages database 
cursor = conn.cursor()              #leads you send sql commands to the database "middleman" / runs sql statements 

# create table
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

conn.commit()   #makes sure changes are saved 
conn.close()    #prevents memory leaks 
