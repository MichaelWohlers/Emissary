# app.py
from flask import Flask
from dotenv import load_dotenv
import os
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('MY_FLASK_SECRET_KEY')
    socketio.init_app(app, cors_allowed_origins="*")

    return app, socketio
