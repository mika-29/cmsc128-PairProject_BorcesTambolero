#this is the main application where it includes all the features for logging in and the main todo list
#initializes the main flask app, loads the login and todo blueprints from their separate files, register those blueprints 
#so their routes become part of the application
#basically the central hub that gathers all modules of the app and starts everything

from flask import Flask
from login import login_bp       #getting the features 
from backend import todo_bp      #getting the featrues

app = Flask(__name__)
app.secret_key = "encrypt_key"

# Register blueprints
app.register_blueprint(login_bp)    #actually connecting the features so it becomes usable
app.register_blueprint(todo_bp)     #so when we call routes, its gonna be @login_app.route()/@todo_bp.route()

if __name__ == "__main__":
    app.run(debug=True)

#so now when the user calls "/", it will go one of those routes that has starts with that.
