from flask import Blueprint, request, jsonify, session
import sqlite3

collab_bp = Blueprint("collab", __name__)

DATABASE = "app.db" 


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn 

@collab_bp.route('/collab/create', methods=['POST'])
def create_collab():
    try:
        data = request.json
        title = data.get('title')
        emails = data.get('emails', [])

        user_id = session.get("u_id")
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401

        # Connect to DB
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()

        # Check all emails exist before creating the list
        for email in emails:
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            user_row = cur.fetchone()
            if not user_row:
                conn.close()
                return jsonify({"error": f"User with email {email} not found"}), 400

        # All emails valid, now insert the collaborative list
        cur.execute(
            "INSERT INTO collab_lists (title, owner_id) VALUES (?, ?)",
            (title, user_id)
        )
        list_id = cur.lastrowid

        # Insert members into collab_members table
        for email in emails:
            cur.execute(
                "INSERT INTO collab_members (list_id, user_email) VALUES (?, ?)",
                (list_id, email)
            )

        conn.commit()
        conn.close()

        return jsonify({"message": "Collaborative list created", "list_id": list_id})

    except Exception as e:
        print("ERROR in /collab/create:", e)
        return jsonify({"error": str(e)}), 500
    
@collab_bp.route('/collab/mylists', methods=['GET'])
def my_collab_lists():
    user_email = session.get("email")

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.title, c.owner_id, c.created_at
        FROM collab_lists c
        JOIN collab_members m ON c.id = m.list_id
        WHERE m.user_email = ?
    """, (user_email,))

    rows = cur.fetchall()
    conn.close()

    lists = [
        {"id": r[0], "title": r[1], "owner_id": r[2], "created_at": r[3]}
        for r in rows
    ]

    return jsonify(lists) 

@collab_bp.route('/collab/tasks/<int:list_id>', methods=['GET'])
def collab_tasks(list_id):
    conn = sqlite3.connect(DATABASE) 
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, status, priority, deadline, duetime, created_at
        FROM collab_tasks
        WHERE list_id = ?
    """, (list_id,))

    rows = cur.fetchall()
    conn.close()

    tasks = [
        {
            "id": r[0], "title": r[1], "status": r[2],
            "priority": r[3], "deadline": r[4], "duetime": r[5],
            "created_at": r[6]
        }
        for r in rows
    ]

    return jsonify(tasks) 

@collab_bp.route('/collab/tasks', methods=['POST'])
def add_collab_task():
    data = request.json
    conn = sqlite3.connect(DATABASE) 
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO collab_tasks (list_id, title, status, priority, deadline, duetime)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data["list_id"], data["title"], data["status"], 
          data["priority"], data["deadline"], data["duetime"]))

    conn.commit()
    conn.close()
    return jsonify({"message": "Task added"}) 

@collab_bp.route('/collab/tasks/<int:task_id>', methods=['PUT'])
def update_collab_task(task_id):
    data = request.json

    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        UPDATE collab_tasks
        SET title=?, status=?, priority=?, deadline=?, duetime=?
        WHERE id=?
    """, (data["title"], data["status"], data["priority"], 
          data["deadline"], data["duetime"], task_id))

    conn.commit()
    conn.close()
    return jsonify({"message": "Task updated"}) 

@collab_bp.route('/collab/tasks/<int:task_id>', methods=['DELETE'])
def delete_collab_task(task_id):
    conn = sqlite3.connect(DATABASE) 
    cur = conn.cursor()
    cur.execute("DELETE FROM collab_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Task deleted"}) 

