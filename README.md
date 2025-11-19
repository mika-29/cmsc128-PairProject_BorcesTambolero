# TO-DO TO-BE, Todo List App
## Backend Used:
Flask + sqlite3 (for database)

## How To Run the WebApp:
- Run "main_app.y"
- Visit the given link provided by Flask
- Sign Up and Log In
- Add personal/collab lists

## API Endpoints:
- For personal to-do endpoints:
    - /tasks (GETTING and POST)
    - /todo (Landing Page)
    -/tasks /<task_id> (UPDATE and DELETE)

- For collaborative to-do endpoints:
    - /collab/mylists (GET all collaborative lists)
    - /collab/tasks/<task_id> (PUTTING, POST, etc..)

- For authentication:
    - "/" (Login)
    - /signup
    - /logout
