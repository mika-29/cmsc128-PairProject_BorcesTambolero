from flask import Flask, request, render_template, session, redirect, url_for, jsonify, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "encrypt_key"

DATABASE = "user.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
            email = request.form.get("email", "").strip()
            pwd = request.form.get("password", "").strip()

            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND password = ?", (email, pwd)
            ).fetchone()
            conn.close()

            if user is None:
                return render_template("login.html", error="Account not found. Please try again.")

            # Login successful → store session
            session["u_id"] = user["id"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        # GET request → just render login page without error
    return render_template("login.html")

# -----------------------------
# SIGNUP / REGISTER ROUTE
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("register.html", step=1)

    # POST request
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    pwd = request.form.get("password", "").strip()

    # Security question fields
    q1 = request.form.get("question1", "").strip()
    a1 = request.form.get("answer1", "").strip()
    q2 = request.form.get("question2", "").strip()
    a2 = request.form.get("answer2", "").strip()
    q3 = request.form.get("question3", "").strip()
    a3 = request.form.get("answer3", "").strip()

    # Validation
    if not (name and email and pwd and q1 and a1 and q2 and a2 and q3 and a3):
        return render_template("register.html", step=2,
                               error="Please complete all security questions.")

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template("register.html", step=1,
                               error="An account with that email already exists.")

    conn.execute(
        """
        INSERT INTO users (name, email, password,
            security_q1, security_ans1, security_q2, security_ans2, security_q3, security_ans3)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (name, email, pwd,
         q1, a1, q2, a2, q3, a3)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            # store email temporarily in session
            session["reset_email"] = email
            return redirect(url_for("change_password"))
        else:
            return render_template("forgot_password.html", error="Email not found.")

    # Default GET request — just show the email input page
    return render_template("forgot_password.html")


# -----------------------------
# CHANGE PASSWORD STEP
# -----------------------------
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("forgot_password"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return redirect(url_for("forgot_password"))

    # Question map
    question_map = {
        "pet": "What was the name of your first pet?",
        "school": "What is the name of your elementary school?",
        "city": "In what city were you born?",
        "nickname": "What is your childhood nickname?",
        "friend": "What is the name of your best friend in high school?",
        "song": "What is your favorite song?",
        "teacher":"What is the name of your favorite teacher?",
        "movie": "What is your favorite movie?",
        "book": "What is your favorite book?",
        "dream": "What is your dream job?",
        "color": "What is your favorite color?",
        "dish": "What is your favorite food?"
    }

    q1 = question_map.get(user["security_q1"], user["security_q1"])
    q2 = question_map.get(user["security_q2"], user["security_q2"])
    q3 = question_map.get(user["security_q3"], user["security_q3"])

    if request.method == "POST":
        ans1 = request.form.get("ans1", "").strip().lower()
        ans2 = request.form.get("ans2", "").strip().lower()
        ans3 = request.form.get("ans3", "").strip().lower()
        new_password = request.form.get("new_password", "").strip()

        if (
            ans1 == user["security_ans1"].lower()
            and ans2 == user["security_ans2"].lower()
            and ans3 == user["security_ans3"].lower()
        ):
            conn = get_db_connection()
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
            conn.commit()
            conn.close()

            session.pop("reset_email", None)
            flash("Password updated successfully! Please log in.", "success")
            return render_template("login.html", message="Password updated successfully! Please log in.")
        else:
            return render_template("change_password.html", q1=q1, q2=q2, q3=q3,
                                   error="One or more answers are incorrect.")

    return render_template("change_password.html", q1=q1, q2=q2, q3=q3)

 #-----------------------------
# CHANGE REQUEST
# -----------------------------
@app.route("/change_request", methods=["GET", "POST"])
def change_request():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            # store email temporarily in session
            session["reset_email"] = email
            return redirect(url_for("question_details"))
        else:
            return render_template("change_request.html", error="Email not found.")

    # Default GET request — just show the email input page
    return render_template("change_request.html")


# -----------------------------
# ANSWER QUESTIONS STEP
# -----------------------------
@app.route("/question_details", methods=["GET", "POST"])
def question_details():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("change_request"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return redirect(url_for("change_request"))

    # Question map
    question_map = {
        "pet": "What was the name of your first pet?",
        "school": "What is the name of your elementary school?",
        "city": "In what city were you born?",
        "nickname": "What is your childhood nickname?",
        "friend": "What is the name of your best friend in high school?",
        "song": "What is your favorite song?",
        "teacher":"What is the name of your favorite teacher?",
        "movie": "What is your favorite movie?",
        "book": "What is your favorite book?",
        "dream": "What is your dream job?",
        "color": "What is your favorite color?",
        "dish": "What is your favorite food?"
    }

    q1 = question_map.get(user["security_q1"], user["security_q1"])
    q2 = question_map.get(user["security_q2"], user["security_q2"])
    q3 = question_map.get(user["security_q3"], user["security_q3"])

    if request.method == "POST":
        ans1 = request.form.get("ans1", "").strip().lower()
        ans2 = request.form.get("ans2", "").strip().lower()
        ans3 = request.form.get("ans3", "").strip().lower()

        if (
            ans1 == user["security_ans1"].lower()
            and ans2 == user["security_ans2"].lower()
            and ans3 == user["security_ans3"].lower()
        ):
            return redirect(url_for("change_details"))
        else: 
            return render_template("question_details.html", q1=q1, q2=q2, q3=q3,
                                   error="One or more answers are incorrect.")

    return render_template("question_details.html", q1=q1, q2=q2, q3=q3)

#-----------------------------
# CHANGE DETAILS
#-----------------------------
@app.route("/change_details", methods=["GET", "POST"])
def change_details():
# Get the email of the user from the session (set after security questions)
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("change_request"))  # or login

    if request.method == "POST":
        name = request.form.get("name")
        new_email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if not user:
            conn.close()
            return redirect(url_for("login"))

        # Check current password
        if current_password != user["password"]:
            conn.close()
            error = "Current password is incorrect."
            return render_template("change_details.html", error=error)

        # Check new password confirmation
        if new_password != confirm_password:
            conn.close()
            error = "New password and confirmation do not match."
            return render_template("change_details.html", error=error)

        # Everything is valid → update user details
        conn.execute(
            "UPDATE users SET name = ?, email = ?, password = ? WHERE email = ?",
            (name, new_email, new_password, email)
        )
        conn.commit()
        conn.close()

        # Clear session and redirect to login
        session.pop("reset_email", None)
        flash("Details updated successfully! Please log in.", "success")
        return render_template("login.html", messsage="Details updated successfully! Please log in.")

    # GET request → show form
    return render_template("change_details.html")

# -----------------------------
# USERS ROUTE (VIEW)
# -----------------------------
@app.route("/users", methods=["GET"])
def get_users():
    sort_by = request.args.get("sort", "id DESC")

    conn = get_db_connection()
    users = conn.execute(
        f"SELECT id, name, email, password, security_q1, security_ans1, security_q2, security_ans2, security_q3, security_ans3 FROM users ORDER BY {sort_by}"
    ).fetchall()
    conn.close()

    return jsonify([dict(user) for user in users])


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "u_id" not in session:
        return redirect(url_for("index"))
    return f"Welcome, {session['name']}!"


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)
