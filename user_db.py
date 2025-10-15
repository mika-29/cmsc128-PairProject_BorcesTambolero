import sqlite3

conn = sqlite3.connect("user.db")   #manages database 
cursor = conn.cursor()              #leads you send sql commands to the database "middleman" / runs sql statements 

# create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
""")

conn.commit()   #makes sure changes are saved 
conn.close()    #prevents memory leaks 
