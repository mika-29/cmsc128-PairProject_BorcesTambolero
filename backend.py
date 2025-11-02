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

    # Add task
    if request.method == "POST":
        title = request.form.get("title")
        if title:
            conn.execute("INSERT INTO tasks (id, title, status, priority) VALUES (?, ?, 'pending', 'mid')",
                         (id, title))
            conn.commit()

    # Get user tasks
    tasks = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchall()
    conn.close()
    return render_template("todo.html", tasks=tasks)

# -------- API to get tasks --------
@todo_bp.route("/tasks", methods=["GET"])
def get_tasks():
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    id = session["u_id"]
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])

# -------- API to delete task --------
@todo_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    id = session["u_id"]
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ? AND id = ?", (task_id, id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
