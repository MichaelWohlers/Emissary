#app.py
from flask import Flask
from dotenv import load_dotenv
import os
from flask_socketio import SocketIO

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('MY_FLASK_SECRET_KEY')

    # Initialize Flask-SocketIO
    # If you're strictly on the same domain and protocol, cors_allowed_origins can be set to '*'
    # This is generally safe for same-origin deployments but be cautious about using '*' in a production environment
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Import and configure routes
    from routes import configure_routes
    configure_routes(app)

    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    # Note: When running on Heroku, you might not need to specify host and port, Heroku sets it for you
    socketio.run(app, debug=True)
