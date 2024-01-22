from flask import Flask
from shared import db
from flask_migrate import Migrate
from routes import configure_routes
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


# Use environment variables for configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

configure_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)