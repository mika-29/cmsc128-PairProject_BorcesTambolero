from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import sqlite3

todo_bp = Blueprint("todo", __name__)

DATABASE = "app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------- Todo Page (renders HTML) --------
@todo_bp.route("/todo")
def todo():
    if "u_id" not in session:
        return redirect(url_for("login.index"))
    return render_template("todo.html")  # JS will fetch tasks via /tasks API

# -------- API to get tasks (personal + collaborative) --------
@todo_bp.route("/tasks", methods=["GET"])
def get_tasks():
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    conn = get_db_connection()
    
    tasks = conn.execute("""
        SELECT DISTINCT t.*
        FROM tasks t
        LEFT JOIN task_collaborators tc ON t.task_id = tc.task_id
        WHERE t.owner_id = ? OR tc.user_id = ?
        ORDER BY t.created_at DESC
    """, (user_id, user_id)).fetchall()
    
    conn.close()

    task_list = []
    for t in tasks:
        task_list.append({
            "id": t["task_id"],
            "title": t["title"],
            "status": t["status"],
            "priority": t["priority"],
            "deadline": t["deadline"],
            "duetime": t["duetime"],
            "created_at": t["created_at"]
        })
    return jsonify(task_list)

# -------- API to add a new task --------
@todo_bp.route("/tasks", methods=["POST"])
def add_task():
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    data = request.get_json()
    title = data.get("title")
    if not title:
        return jsonify({"error": "Title required"}), 400

    deadline = data.get("deadline")
    duetime = data.get("duetime")
    status = data.get("status") or "pending"
    priority = data.get("priority") or "mid"
    collaborators = data.get("collaborators") or []

    conn = get_db_connection()
    cur = conn.execute(
        "INSERT INTO tasks (owner_id, title, deadline, duetime, status, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, title, deadline, duetime, status, priority)
    )
    task_id = cur.lastrowid

    # Add collaborators
    for c_id in collaborators:
        conn.execute(
            "INSERT OR IGNORE INTO task_collaborators (task_id, user_id, role) VALUES (?, ?, ?)",
            (task_id, c_id, "editor")
        )

    conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()

    return jsonify({
        "id": task["task_id"],
        "title": task["title"],
        "status": task["status"],
        "priority": task["priority"],
        "deadline": task["deadline"],
        "duetime": task["duetime"],
        "created_at": task["created_at"]
    }), 201

# -------- API to update a task --------
@todo_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    data = request.get_json()
    fields = []
    values = []

    for field in ["title", "deadline", "duetime", "status", "priority"]:
        if field in data:
            fields.append(f"{field}=?")
            values.append(data[field])

    if not fields:
        return jsonify({"error": "No valid fields provided"}), 400

    values.append(task_id)
    conn = get_db_connection()
    conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE task_id=? AND owner_id=?", tuple(values + [user_id]))
    conn.commit()
    conn.close()

    return jsonify({"message": "Task updated!"})

# -------- API to delete a task --------
@todo_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    if "u_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["u_id"]
    conn = get_db_connection()
    cur = conn.execute("DELETE FROM tasks WHERE task_id=? AND owner_id=?", (task_id, user_id))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": "Task not found or you are not the owner"}), 404

    return jsonify({"success": True})

# Delete a collaborative space (collab list)
@todo_bp.route('/collab/delete/<int:list_id>', methods=['DELETE'])
def delete_collab_list(list_id):
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user_id = session['u_id']
    conn = get_db_connection()
    # Check ownership
    owner = conn.execute('SELECT owner_id FROM collab_lists WHERE id = ?', (list_id,)).fetchone()
    if not owner:
        conn.close()
        return jsonify({'error': 'Collaborative list not found'}), 404
    if owner['owner_id'] != user_id:
        conn.close()
        return jsonify({'error': 'Not authorized to delete this collaborative space'}), 403
    # Delete all related tasks and members
    conn.execute('DELETE FROM collab_tasks WHERE list_id = ?', (list_id,))
    conn.execute('DELETE FROM collab_members WHERE list_id = ?', (list_id,))
    conn.execute('DELETE FROM collab_lists WHERE id = ?', (list_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})