"""Two separate MySQL connections:
   - app_conn(): stores progress (account can only touch the app database)
   - lab_conn(): runs the learner's SQL (account can only touch the sandbox database)"""
import mysql.connector
from config import Config as C


def app_conn():
    return mysql.connector.connect(
        host=C.DB_HOST, port=C.DB_PORT, user=C.APP_DB_USER, password=C.APP_DB_PASSWORD,
        database=C.APP_DB_NAME, autocommit=True, connection_timeout=5)


def lab_conn():
    return mysql.connector.connect(
        host=C.DB_HOST, port=C.DB_PORT, user=C.LAB_DB_USER, password=C.LAB_DB_PASSWORD,
        database=C.LAB_DB_NAME, autocommit=True, connection_timeout=5)


def query(sql, params=None, one=False):
    """Run a SELECT on the app database and return dict rows (always parameterized)."""
    conn = app_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, params=None):
    """Run INSERT/UPDATE/DELETE on the app database. Returns the new row id."""
    conn = app_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        return cur.lastrowid
    finally:
        conn.close()


def is_connected():
    try:
        app_conn().close()
        lab_conn().close()
        return True
    except Exception:
        return False
