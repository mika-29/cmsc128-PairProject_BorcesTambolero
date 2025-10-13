from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

DATABASE = "user.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # allows dict-like row access
    return conn

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    pwd = request.form.get('password', '').strip()

    if not name or not email or not pwd:
        return jsonify({"error": "Please enter your name, email, and password"}), 400
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND name = ?", (email, name)).fetchone()
    conn.close()

    if user is None:
        return jsonify({"error": "Invalid credentials"}), 401

    if pwd != user['password']:
        return jsonify({"error": "Invalid name, email, or password"}), 401

    session['u_id'] = user['id']
    session['name'] = user['name']

    return jsonify({"message": "success"}), 200
