from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import sqlite3

todo_bp = Blueprint("todo", __name__)

DATABASE = "app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Collaborative lists & tasks endpoints ----------
@todo_bp.route('/collab/create', methods=['POST'])
def create_collab_list():
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json() or {}
    title = data.get('title')
    emails = data.get('emails', [])

    if not title:
        return jsonify({'error': 'Title required'}), 400

    owner_id = session['u_id']
    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO collab_lists (title, owner_id) VALUES (?, ?)',
        (title, owner_id)
    )
    list_id = cur.lastrowid

    # insert members (store emails as provided)
    for em in emails:
        if not em:
            continue
        conn.execute(
            'INSERT INTO collab_members (list_id, user_email) VALUES (?, ?)',
            (list_id, em)
        )

    conn.commit()
    conn.close()

    return jsonify({'list_id': list_id, 'title': title, 'owner_id': owner_id}), 201


@todo_bp.route('/collab/mylists', methods=['GET'])
def get_my_collab_lists():
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['u_id']
    conn = get_db_connection()

    # Lists owned by user
    owned = conn.execute(
        'SELECT id, title, owner_id, created_at FROM collab_lists WHERE owner_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()

    # Lists where user is a member (match users table via email)
    member_lists = conn.execute(
        '''
        SELECT DISTINCT cl.id, cl.title, cl.owner_id, cl.created_at
        FROM collab_lists cl
        JOIN collab_members cm ON cl.id = cm.list_id
        LEFT JOIN users u ON u.email = cm.user_email
        WHERE u.id = ?
        ORDER BY cl.created_at DESC
        ''',
        (user_id,)
    ).fetchall()

    results = []
    seen = set()
    for row in owned + member_lists:
        if row['id'] in seen:
            continue
        seen.add(row['id'])
        results.append({
            'id': row['id'],
            'title': row['title'],
            'owner_id': row['owner_id'],
            'created_at': row['created_at']
        })

    conn.close()
    return jsonify(results)


@todo_bp.route('/collab/tasks', methods=['POST'])
def create_collab_task():
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json() or {}
    list_id = data.get('list_id')
    title = data.get('title')
    if not list_id or not title:
        return jsonify({'error': 'list_id and title required'}), 400

    status = data.get('status', 'pending')
    priority = data.get('priority', 'mid')
    deadline = data.get('deadline')
    duetime = data.get('duetime')

    conn = get_db_connection()
    # simple membership check: allow if owner or member
    owner = conn.execute('SELECT owner_id FROM collab_lists WHERE id = ?', (list_id,)).fetchone()
    if not owner:
        conn.close()
        return jsonify({'error': 'List not found'}), 404

    # optional: check membership or owner
    # For now we allow creation if user is the owner or listed as a member (by email)
    user_id = session['u_id']
    allowed = False
    if owner['owner_id'] == user_id:
        allowed = True
    else:
        # check member table for user's email
        user_row = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_row:
            em = user_row['email']
            member = conn.execute('SELECT id FROM collab_members WHERE list_id = ? AND user_email = ?', (list_id, em)).fetchone()
            if member:
                allowed = True

    if not allowed:
        conn.close()
        return jsonify({'error': 'Not authorized for this list'}), 403

    cur = conn.execute(
        'INSERT INTO collab_tasks (list_id, title, status, priority, deadline, duetime) VALUES (?, ?, ?, ?, ?, ?)',
        (list_id, title, status, priority, deadline, duetime)
    )
    task_id = cur.lastrowid
    conn.commit()
    task = conn.execute('SELECT * FROM collab_tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()

    return jsonify({
        'id': task['id'],
        'list_id': task['list_id'],
        'title': task['title'],
        'status': task['status'],
        'priority': task['priority'],
        'deadline': task['deadline'],
        'duetime': task['duetime'],
        'created_at': task['created_at']
    }), 201


@todo_bp.route('/collab/tasks/<int:list_id>', methods=['GET'])
def get_collab_tasks(list_id):
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    conn = get_db_connection()
    # verify access
    owner = conn.execute('SELECT owner_id FROM collab_lists WHERE id = ?', (list_id,)).fetchone()
    if not owner:
        conn.close()
        return jsonify({'error': 'List not found'}), 404

    user_id = session['u_id']
    allowed = False
    if owner['owner_id'] == user_id:
        allowed = True
    else:
        user_row = conn.execute('SELECT email FROM users WHERE id = ?', (user_id,)).fetchone()
        if user_row:
            em = user_row['email']
            member = conn.execute('SELECT id FROM collab_members WHERE list_id = ? AND user_email = ?', (list_id, em)).fetchone()
            if member:
                allowed = True

    if not allowed:
        conn.close()
        return jsonify({'error': 'Not authorized for this list'}), 403

    tasks = conn.execute('SELECT * FROM collab_tasks WHERE list_id = ? ORDER BY created_at DESC', (list_id,)).fetchall()
    result = []
    for t in tasks:
        result.append({
            'id': t['id'],
            'list_id': t['list_id'],
            'title': t['title'],
            'status': t['status'],
            'priority': t['priority'],
            'deadline': t['deadline'],
            'duetime': t['duetime'],
            'created_at': t['created_at']
        })

    conn.close()
    return jsonify(result)


@todo_bp.route('/collab/tasks/<int:task_id>', methods=['DELETE'])
def delete_collab_task(task_id):
    if 'u_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM collab_tasks WHERE id = ?', (task_id,)).fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404

    # allow delete only by list owner
    list_row = conn.execute('SELECT owner_id FROM collab_lists WHERE id = ?', (task['list_id'],)).fetchone()
    if not list_row or list_row['owner_id'] != session['u_id']:
        conn.close()
        return jsonify({'error': 'Not authorized to delete this task'}), 403

    conn.execute('DELETE FROM collab_tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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