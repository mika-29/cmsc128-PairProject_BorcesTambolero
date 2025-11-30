from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import sqlite3

todo_bp = Blueprint("todo", __name__)

DATABASE = "app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------- Todo Page --------
@todo_bp.route("/todo", methods=["GET", "POST"])
def todo():
    if "u_id" not in session:
        return redirect(url_for("login.index"))

    id = session["u_id"] 
    conn = get_db_connection()

    # Get user tasks
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (id,)).fetchall()
    conn.close()
    return render_template("todo.html", tasks=tasks)

#-------------API to add task------------
@todo_bp.route("/tasks", methods=["POST"])
def add_task():
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    user_id = session["u_id"]

    title = data.get("title")
    deadline = data.get("deadline")
    duetime = data.get("duetime")
    status = data.get("status", "pending")
    priority = data.get("priority", "mid")
    created_at = data.get("createdAt") 

    if not title:
        return jsonify({"error": "Title required"}), 400

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO tasks (user_id, title, deadline, duetime, status, priority, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, title, deadline, duetime, status, priority, created_at))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# -------- API to get tasks --------
@todo_bp.route("/tasks", methods=["GET"])
def get_tasks():
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, title, deadline, duetime, status, priority, created_at
        FROM tasks
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

#----------- API to edit tasks --------------
@todo_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def edit_task(task_id):
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data sent"}), 400

    title = data.get("title")
    deadline = data.get("deadline")
    duetime = data.get("duetime")
    status = data.get("status")
    priority = data.get("priority")
    created_at = data.get("createdAt")  # JS sends createdAt

    conn = get_db_connection()
    conn.execute("""
        UPDATE tasks
        SET title = ?, deadline = ?, duetime = ?, status = ?, priority = ?, created_at = ?
        WHERE id = ? AND user_id = ?
    """, (title, deadline, duetime, status, priority, created_at, task_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# -------- API to delete task --------
@todo_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Task not found or not yours"}), 404

    return jsonify({"success": True})