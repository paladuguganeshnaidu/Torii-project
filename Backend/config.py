import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DB_DIR = os.path.join(PROJECT_ROOT, 'database')
DB_PATH = os.path.join(DB_DIR, 'app.db')
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'database', 'schema.sql')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DATABASE = DB_PATH
    TEMPLATES_AUTO_RELOAD = True
