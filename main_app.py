from flask import Flask
from login import login_bp
from backend import todo_bp

app = Flask(__name__)
app.secret_key = "encrypt_key"

@app.after_request
def add_header(response):

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(todo_bp)

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)
