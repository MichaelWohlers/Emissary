from flask import Flask
from dotenv import load_dotenv
import os
from shared import celery  # Import the Celery instance from shared.py
from tasks import execute_query_and_fetch_data


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # Use environment variables for configuration
    app.config['SECRET_KEY'] = os.environ.get('MY_FLASK_SECRET_KEY')
    app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL')

    # Configure the Celery instance from shared.py with the app's settings
    celery.conf.update(app.config)

    # Import and configure routes
    from routes import configure_routes
    configure_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
