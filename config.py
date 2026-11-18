"""Central configuration. Values come from the .env file (never sent to the browser)."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))

    APP_DB_NAME = os.getenv("APP_DB_NAME", "magi_app")
    APP_DB_USER = os.getenv("APP_DB_USER", "magi_app")
    APP_DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "")

    LAB_DB_NAME = os.getenv("LAB_DB_NAME", "magi_lab")
    LAB_DB_USER = os.getenv("LAB_DB_USER", "magi_learner")
    LAB_DB_PASSWORD = os.getenv("LAB_DB_PASSWORD", "")

    MAX_ROWS = 200            # rows shown per result set
    MAX_STATEMENTS = 20       # statements per run
    QUERY_TIMEOUT_MS = 5000   # SELECT time limit
    EXAM_PASS_PERCENT = 70
