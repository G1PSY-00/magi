# MAGI SQL ACADEMY

Local SQL learning platform (Flask + MySQL) with an Evangelion / NERV orange terminal look.

## Setup (Windows CMD)

```cmd
cd magi_sql_academy
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```
1. Open `.env` and change the two passwords (`APP_DB_PASSWORD`, `LAB_DB_PASSWORD`) and `SECRET_KEY`.
2. Make sure the MySQL service is running (MySQL 8.0+ is required for window functions and CTEs).
3. Create the databases, the two restricted accounts, the tables and the sample data (asks for your MySQL admin login once; it is not stored):
```cmd
python setup_db.py
```
4. Start the app and open http://127.0.0.1:5000
```cmd
python app.py
```
Next time: `cd magi_sql_academy`, `venv\Scripts\activate`, `python app.py`.

## How the safety works
* `magi_app` account: can only touch the progress database `magi_app`.
* `magi_learner` account: can only touch the sandbox `magi_lab`. Your learner SQL runs ONLY through this account.
* A text filter also blocks system schemas, file access, user/server admin commands, CREATE/DROP DATABASE, USE other_db, SLEEP.
* DROP, TRUNCATE and UPDATE/DELETE without WHERE ask for confirmation. SELECTs have a 5 s limit, results show max 200 rows, max 20 statements per run.
* Stored procedures/functions/triggers are sent as one statement; `CALL name(literal, ...)` is supported. Transactions work inside one editor run (an unfinished one is rolled back).

## Adding content
* Lessons: append a `lesson(...)` entry in `content/lessons.py`.
* Practice / exam questions: add to `content/exercises.py` (`EXERCISES`, `QUESTIONS`, `DEBUG`).
* New sample database: add `database/scenarios/<name>.sql` and register it in `SCENARIOS` in `services/sql_executor.py`.

## Troubleshooting
* `DATABASE DISCONNECTED` chip: MySQL not running, `setup_db.py` not run, or `.env` passwords differ from the ones used in setup (re-run `setup_db.py`, it resets the account passwords).
* `Access denied` in setup_db.py: wrong admin password. `mysql` not recognized: not needed, setup uses Python.
* `Authentication plugin 'caching_sha2_password'` errors: `pip install --upgrade mysql-connector-python`.
* Editor looks like a plain box: CodeMirror loads from cdnjs, so highlighting needs internet; everything else works offline.
* Stored functions error about `log_bin_trust_function_creators`: run `SET GLOBAL log_bin_trust_function_creators = 1;` as admin.
* Port 5000 busy: change the port at the bottom of `app.py`.
