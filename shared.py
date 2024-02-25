from flask_sqlalchemy import SQLAlchemy
from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Celery without the app context
celery = Celery(__name__, broker=os.environ.get('CELERY_BROKER_URL'))

db = SQLAlchemy()
