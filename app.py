from flask import Flask
from shared import db
from flask_migrate import Migrate
from routes import configure_routes
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


# Use environment variables for configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')




configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)