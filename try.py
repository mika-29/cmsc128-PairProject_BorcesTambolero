import sqlite3

conn = sqlite3.connect("app.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

user = c.execute("SELECT id, name, email, security_q1, security_ans1 FROM users").fetchall()
for u in user:
    print(dict(u))
conn.close()
