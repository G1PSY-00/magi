"""One-time setup. Run:  python setup_db.py
Asks for your MySQL ADMIN login (e.g. root) ONCE, creates the two databases and the two
restricted accounts from your .env file, then creates tables and loads the sample data.
The admin password is never stored anywhere."""
import getpass
from pathlib import Path
import mysql.connector
from config import Config as C
from services.sql_executor import split_statements, load_scenario

BASE = Path(__file__).parent / "database"


def run_file(cur, path):
    for stmt in split_statements(path.read_text(encoding="utf-8")):
        cur.execute(stmt)


def main():
    admin = input("MySQL admin user [root]: ").strip() or "root"
    pw = getpass.getpass("MySQL admin password: ")
    conn = mysql.connector.connect(host=C.DB_HOST, port=C.DB_PORT, user=admin, password=pw)
    cur = conn.cursor()
    for db, user, pwd in ((C.APP_DB_NAME, C.APP_DB_USER, C.APP_DB_PASSWORD),
                          (C.LAB_DB_NAME, C.LAB_DB_USER, C.LAB_DB_PASSWORD)):
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4")
        cur.execute(f"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY %s", (pwd,))
        cur.execute(f"ALTER USER '{user}'@'localhost' IDENTIFIED BY %s", (pwd,))
        # Each account gets rights on ITS OWN database only.
        cur.execute(f"GRANT ALL PRIVILEGES ON `{db}`.* TO '{user}'@'localhost'")
    cur.execute("FLUSH PRIVILEGES")
    try:  # lets learners create stored functions when binary logging is on
        cur.execute("SET GLOBAL log_bin_trust_function_creators = 1")
    except mysql.connector.Error:
        print("(note) could not set log_bin_trust_function_creators; stored functions may need it.")
    cur.execute(f"USE `{C.APP_DB_NAME}`")
    run_file(cur, BASE / "schema.sql")
    run_file(cur, BASE / "seed.sql")
    conn.close()
    load_scenario("school")
    print("Done. Start the app with:  python app.py")


if __name__ == "__main__":
    main()
