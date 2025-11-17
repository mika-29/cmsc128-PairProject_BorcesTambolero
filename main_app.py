from flask import Flask
from login import login_bp
from backend import todo_bp
from collab import collab_bp

app = Flask(__name__)
app.secret_key = "encrypt_key"

# Register blueprints
app.register_blueprint(login_bp)
app.register_blueprint(todo_bp)
app.register_blueprint(collab_bp)

if __name__ == "__main__":
    app.run(debug=True)
