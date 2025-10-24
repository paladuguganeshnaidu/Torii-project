import os

# Paths used by the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
DB_DIR = os.path.join(PROJECT_ROOT, 'database')
DB_PATH = os.path.join(DB_DIR, 'app.db')
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'database', 'schema.sql')


class Config:
    """Central configuration for the Flask app.

    Note: This module should only define configuration and constants.
    The Flask app factory and blueprint registrations live in Backend/app.py.
    """

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DATABASE = DB_PATH
    TEMPLATES_AUTO_RELOAD = True


# DoS detector configuration (tunable)
DOS_CONFIG = {
    "whitelist": [
        "127.0.0.1",
        "192.168.1.0/24",
        "10.0.0.0/8"
    ],
    "thresholds": {
        "pps_global": 10000,
        "req_per_ip": 100
    },
    "z_score_window": 900  # 15 minutes
}

