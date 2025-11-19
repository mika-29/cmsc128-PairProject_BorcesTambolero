from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import sqlite3

collab_bp = Blueprint("collab", __name__)

DATABASE = "app.db" 


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn 

# ---------- Collaborative lists & tasks endpoints ----------
@collab_bp.route('/collab/create', methods=['POST'])
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

    # Check all emails exist in users table
    for em in emails:
        if not em:
            continue
        user = conn.execute('SELECT id FROM users WHERE email = ?', (em,)).fetchone()
        if not user:
            conn.close()
            return jsonify({'error': f'User not found: {em}'}), 400

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
    # fetch member display names (name if available, otherwise email)
    members = []
    rows = conn.execute(
        'SELECT cm.user_email, u.name FROM collab_members cm LEFT JOIN users u ON u.email = cm.user_email WHERE cm.list_id = ?',
        (list_id,)
    ).fetchall()
    for r in rows:
        members.append(r['name'] if r['name'] else r['user_email'])

    conn.close()

    return jsonify({'list_id': list_id, 'title': title, 'owner_id': owner_id, 'members': members}), 201


@collab_bp.route('/collab/mylists', methods=['GET'])
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
        # fetch members for this list
        mem_rows = conn.execute(
            'SELECT cm.user_email, u.name FROM collab_members cm LEFT JOIN users u ON u.email = cm.user_email WHERE cm.list_id = ?',
            (row['id'],)
        ).fetchall()
        members = [m['name'] if m['name'] else m['user_email'] for m in mem_rows]

        results.append({
            'id': row['id'],
            'title': row['title'],
            'owner_id': row['owner_id'],
            'created_at': row['created_at'],
            'members': members
        })

    conn.close()
    return jsonify(results)


@collab_bp.route('/collab/tasks', methods=['POST'])
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


@collab_bp.route('/collab/tasks/<int:list_id>', methods=['GET'])
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


@collab_bp.route('/collab/tasks/<int:task_id>', methods=['DELETE'])
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