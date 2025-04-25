# run.py
from app import create_app, db  # Import db if needed for shell context
from app.models import User, DiaryEntry  # Import models for shell context

app = create_app()


# Add shell context processor for `flask shell`
@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "DiaryEntry": DiaryEntry}


if __name__ == "__main__":
    # Set host='0.0.0.0' to make it accessible on your network
    # Use debug=True only in development
    app.run(host="0.0.0.0", port=5001, debug=True)
