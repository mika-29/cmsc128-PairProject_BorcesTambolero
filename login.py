from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

login_bp = Blueprint("login", __name__) #creates basically a module that includes all routes within it so it can be registered in the main app
DATABASE = "app.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# LOGIN ROUTE
# -----------------------------
@login_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        pwd = request.form.get("password", "").strip()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user is None:
            return render_template("login.html", error="Account not found. Please try again.")

        if user and check_password_hash(user["password"], pwd):
            session["u_id"] = user["id"]
            session["name"] = user["name"]
            
            return redirect(url_for("todo.todo"))  # redirect to your todo page
        else:
            return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


# -----------------------------
# SIGNUP / REGISTER ROUTE
# -----------------------------
@login_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("register.html", step=1)

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    pwd = request.form.get("password", "").strip()
    hashed_password = generate_password_hash(pwd)

    q1 = request.form.get("question1", "").strip()
    a1 = request.form.get("answer1", "").strip()
    hashed_answer = generate_password_hash(a1)

    if not (name and email and pwd and q1 and a1):
        return render_template("register.html", step=2,
                               error="Please complete all fields including security question.")

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return render_template("register.html", step=1, error="An account with that email already exists.")

    conn.execute(
        """
        INSERT INTO users (name, email, password, security_q1, security_ans1)
        VALUES (?, ?, ?, ?, ?)
        """, 
        (name, email, hashed_password, q1, hashed_answer))
    conn.commit()
    conn.close()

    return redirect(url_for("login.index"))


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@login_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
             # store email temporarily in session
            session["reset_email"] = email
            return redirect(url_for("login.change_password"))
        else:
            return render_template("forgot_password.html", error="Email not found.")
        
    # Default GET request — just show the email input page
    return render_template("forgot_password.html")


# -----------------------------
# CHANGE PASSWORD STEP
# -----------------------------
@login_bp.route("/change_password", methods=["GET", "POST"])
def change_password():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("login.forgot_password"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return redirect(url_for("login.forgot_password"))

    question_map = {
        "pet": "What was the name of your first pet?",
        "school": "What is the name of your elementary school?",
        "city": "In what city were you born?",
        "nickname": "What is your childhood nickname?"
    }

    q1 = question_map.get(user["security_q1"], user["security_q1"])

    if request.method == "POST":
        ans1 = request.form.get("ans1", "").strip().lower()
        new_password = request.form.get("new_password", "").strip()

        if check_password_hash(user["security_ans1"], ans1):
            hashed_new_password = generate_password_hash(new_password)
            conn = get_db_connection()
            conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_new_password, email))
            conn.commit()
            conn.close()

            session.pop("reset_email", None)
            flash("Password updated successfully! Please log in.", "success")
            return redirect(url_for("login.index"))
        else:
            return render_template("change_password.html", q1=q1,
                                   error="Your answer is incorrect.")

    return render_template("change_password.html", q1=q1)


# -----------------------------
# CHANGE REQUEST
# -----------------------------
@login_bp.route("/change_request", methods=["GET", "POST"])
def change_request():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            # store email temporarily in session
            session["reset_email"] = email
            return redirect(url_for("login.question_details"))
        else:
            return render_template("change_request.html", error="Email not found.")

    # Default GET request — just show the email input page
    return render_template("change_request.html")

# -----------------------------
# ANSWER QUESTIONS STEP
# -----------------------------
@login_bp.route("/question_details", methods=["GET", "POST"])
def question_details():
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("login.change_request"))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        return redirect(url_for("login.change_request"))

    # Question map
    question_map = {
        "pet": "What was the name of your first pet?",
        "school": "What is the name of your elementary school?",
        "city": "In what city were you born?",
        "nickname": "What is your childhood nickname?"
    }

    q1 = question_map.get(user["security_q1"], user["security_q1"])

    if request.method == "POST":
        ans1 = request.form.get("ans1", "").strip().lower()

        if (check_password_hash(user["security_ans1"], ans1)):
            return redirect(url_for("login.change_details"))
        else: 
            return render_template("question_details.html", q1=q1,
                                   error="Your answer is incorrect.")

    return render_template("question_details.html", q1=q1)

#-----------------------------
# CHANGE DETAILS
#-----------------------------
@login_bp.route("/change_details", methods=["GET", "POST"])
def change_details():
# Get the email of the user from the session (set after security questions)
    email = session.get("reset_email")
    if not email:
        return redirect(url_for("login.change_request"))  # or login

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
            return redirect(url_for("login.change_request"))

        # Check current password
        if not check_password_hash(user["password"], current_password):
            conn.close()
            error = "Current password is incorrect."
            return render_template("change_details.html", error=error)

        # Check new password confirmation
        if new_password != confirm_password:
            conn.close()
            error = "New password and confirmation do not match."
            return render_template("change_details.html", error=error)

        # Everything is valid → update user details
        hashed_new_password = generate_password_hash(new_password)
        conn.execute(
            "UPDATE users SET name = ?, email = ?, password = ? WHERE email = ?",
            (name, new_email, hashed_new_password, email)
            )
        conn.commit()
        conn.close()

         # Clear session and redirect
        session.pop("reset_email", None)
        flash("Details updated successfully! Please log in.", "success")
        return redirect(url_for("login.index"))

    # GET request → show form
    return render_template("change_details.html")

# -----------------------------
# LOGOUT
# -----------------------------
@login_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login.index"))
