"""Checks learner answers by comparing RESULTS, never SQL text, so many valid solutions work.
 - kind "select": run learner SQL and the reference solution, compare result sets.
 - kind "dml":    run each on a freshly reset sandbox and compare the resulting table state."""
import re
from services.sql_executor import run_script, load_scenario

NUM = re.compile(r"^-?\d+(\.\d+)?$")


def _norm(v):
    if v is None:
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and NUM.match(v.strip())):
        return round(float(v), 4)
    return str(v).strip()


def _last_rows(run):
    for r in reversed(run.get("results", [])):
        if r["type"] == "rows":
            return r
    return None


def _compare(user, ref, ordered):
    if user is None:
        return False, "Your SQL ran, but it did not return a result table. This exercise needs a SELECT-style result."
    if len(user["columns"]) != len(ref["columns"]):
        return False, f"Your result has {len(user['columns'])} column(s) but the task needs {len(ref['columns'])}. Re-read which columns are requested."
    u = [tuple(_norm(v) for v in r) for r in user["rows"]]
    e = [tuple(_norm(v) for v in r) for r in ref["rows"]]
    if len(u) != len(e):
        return False, f"Your query returned {len(u)} row(s) but {len(e)} were expected. Check your WHERE / JOIN / GROUP BY conditions."
    key = lambda t: repr(t)
    if sorted(u, key=key) != sorted(e, key=key):
        return False, "The number of rows is right, but some values differ. Check the columns you selected and your conditions."
    if ordered and u != e:
        return False, "You have the right rows, but the ORDER matters here. Check your ORDER BY."
    return True, "Result matches."


def validate(ex, user_sql):
    """Returns {"correct": bool, "message": str}."""
    load_scenario(ex["scenario"])                       # always start from clean data
    user = run_script(user_sql, confirm=True)           # learner SQL goes through safety filters
    if user.get("blocked") or not user.get("results"):
        return {"correct": False, "message": user["error"]["message"]}
    err = next((r for r in user["results"] if r["type"] == "error"), None)
    if err:
        return {"correct": False, "message": "MySQL error: " + err["message"], "error": err}
    if ex.get("kind", "select") == "select":
        ref = _last_rows(run_script(ex["solution"], confirm=True, trusted=True))
        ordered = bool(re.search(r"order\s+by", ex["solution"], re.I))
        ok, msg = _compare(_last_rows(user), ref, ordered)
        return {"correct": ok, "message": msg}
    # DML / DDL: compare the table state after each version
    state_user = _last_rows(run_script(ex["check"], trusted=True))
    load_scenario(ex["scenario"])
    run_script(ex["solution"], confirm=True, trusted=True)
    state_ref = _last_rows(run_script(ex["check"], trusted=True))
    load_scenario(ex["scenario"])                       # leave the sandbox clean
    ok, msg = _compare(state_user, state_ref, False)
    return {"correct": ok, "message": "The database now looks exactly as expected." if ok else
            "Your statement ran, but the resulting data is not what the task asked for. " + msg}
