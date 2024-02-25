# run.py
from app import create_app, socketio

app, socketio = create_app()

# Ensure routes are imported after the app and socketio instances are created
from routes import configure_routes
configure_routes(app)

if __name__ == "__main__":
    socketio.run(app, debug=True)
