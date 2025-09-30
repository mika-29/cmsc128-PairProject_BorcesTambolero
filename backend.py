from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row  # lets us access rows like dictionaries  task["title"] instead of task[1]
    return conn

# Homepage (renders frontend)
@app.route("/")
def index():
    return render_template("todo.html")   # make sure todo.html is in your templates/ folder


# Get all tasks
@app.route("/tasks", methods=["GET"])  
def get_tasks():
    sort_by = request.args.get("sort", "date_added")  # default sort
    
    valid_sorts = {
        "date_added": "id DESC",        # newest first (id = auto increment)
        "deadline": "deadline ASC",     # soonest deadline first
        "priority": """CASE priority
                          WHEN 'important'  THEN 1
                          WHEN 'mid'        THEN 2
                          WHEN 'easy'       THEN 3
                       END ASC"""  # important first, then normal, then low
    }
    order_clause = valid_sorts.get(sort_by, "id DESC")
    conn = get_db_connection()
    tasks = conn.execute(f"SELECT * FROM tasks ORDER BY {order_clause}").fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])  # convert each row into a dict   /return JSON so frontend can use 


# Add a new task
@app.route("/tasks", methods=["POST"])   
def add_task():
    data = request.get_json()

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tasks (title, deadline, duetime, status, priority) VALUES (?, ?, ?, ?, ?)",
        (data["title"], data["deadline"], data["duetime"], data["status"], data["priority"]),
    )
    conn.commit()
    conn.close()


# Update an existing task
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    fields = []
    values = []

    # Build only the fields that are provided
    if "title" in data:
        fields.append("title=?")
        values.append(data["title"])
    if "deadline" in data:
        fields.append("deadline=?")
        values.append(data["deadline"])
    if "duetime" in data:
        fields.append("duetime=?")
        values.append(data["duetime"])
    if "status" in data:
        fields.append("status=?")
        values.append(data["status"])
    if "priority" in data:
        fields.append("priority=?")
        values.append(data["priority"])

    # Build query dynamically
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id=?"
    values.append(task_id)

    conn = get_db_connection()    
    conn.execute(query, tuple(values))
    conn.commit()
    conn.close()


# Delete a task
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    app.run(debug=True)
