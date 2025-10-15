from flask import Flask, request, jsonify, render_template, session
import sqlite3

app = Flask(__name__)
app.secret_key = "encrypt_key"

DATABASE = "user.db"

def get_db_connection():
    conn = sqlite3.connect("user.db")
    conn.row_factory = sqlite3.Row  # allows dict-like row access
    return conn

@app.route("/")
def index():
    return render_template("login.html")   


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    pwd = request.form.get('password', '').strip()

    if not name or not email or not pwd:
        return jsonify({"error": "Please enter your name, email, and password"})
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND name = ?", (email, name)).fetchone()
    conn.close()

    if user is None:
        return jsonify({"error": "Invalid credentials"})

    if pwd != user['password']:
        return jsonify({"error": "Invalid name, email, or password"})

    session['u_id'] = user['id']
    session['name'] = user['name']

    return jsonify({"message": "success"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)

