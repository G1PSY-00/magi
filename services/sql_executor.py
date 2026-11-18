"""Safe SQL execution engine.

Safety layers (outer to inner):
 1. The learner account in MySQL can only access the sandbox database (the REAL protection).
 2. A text filter blocks system schemas, file access, user management, USE other_db, etc.
 3. Dangerous statements (DROP, TRUNCATE, DELETE/UPDATE without WHERE) need confirmation.
 4. A time limit for SELECT and a row limit for results.
"""
import ast
import re
import time
from pathlib import Path
from mysql.connector import Error
from config import Config as C
from database.connection import lab_conn
from services.learning_assistant import explain_error

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "database" / "scenarios"
SCENARIOS = {
    "school": "School Management",
    "employees": "Employee Management",
    "ecommerce": "E-commerce",
}

# (regex on lower-cased SQL without strings/comments, message)
FORBIDDEN = [
    (r"\b(information_schema|performance_schema)\b|\bmysql\s*\.|\bsys\s*\.", "System schemas are off-limits in the sandbox."),
    (r"\binto\s+(outfile|dumpfile)\b|\bload_file\s*\(|\bload\s+data\b", "File access is blocked."),
    (r"\b(grant|revoke|flush|shutdown|kill|install|uninstall)\b|\b(create|alter|drop|rename)\s+user\b|\bset\s+(global|persist|password)\b",
     "Server administration commands are blocked."),
    (r"\b(create|drop)\s+(database|schema)\b",
     "CREATE/DROP DATABASE is disabled: your sandbox database already exists. Use CREATE TABLE instead."),
    (r"\bsleep\s*\(|\bbenchmark\s*\(", "SLEEP/BENCHMARK are blocked so queries cannot freeze the app."),
]
ROUTINE_RE = re.compile(r"^\s*create\s+(definer\s*=\s*\S+\s+)?(procedure|function|trigger)\b", re.I)
CALL_RE = re.compile(r"^\s*call\s+(\w+)\s*\((.*)\)\s*$", re.I | re.S)


def strip_literals(sql):
    """Replace quoted strings with '' and remove comments, scanning left to right so a quote
    inside a comment (or a # inside a string) cannot hide text from the safety checks."""
    pattern = r"""'(?:[^'\\]|\\.|'')*'|"(?:[^"\\]|\\.)*"|(?s:/\*.*?\*/)|--[ \t].*|#.*"""
    return re.sub(pattern, lambda m: "''" if m.group(0)[0] in "'\"" else " ", sql)


def split_statements(sql):
    """Split a script on ';' while ignoring semicolons inside quotes and comments."""
    out, buf, quote, i, n = [], [], None, 0, len(sql)
    while i < n:
        ch = sql[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < n:
                buf.append(sql[i + 1]); i += 1
            elif ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch; buf.append(ch)
        elif sql.startswith("-- ", i) or ch == "#":
            while i < n and sql[i] != "\n":
                i += 1
            continue
        elif sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        elif ch == ";":
            stmt = "".join(buf).strip()
            if stmt: out.append(stmt)
            buf = []
        else:
            buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail: out.append(tail)
    return out


def check_forbidden(stmt):
    clean = strip_literals(stmt).lower()
    for pattern, msg in FORBIDDEN:
        if re.search(pattern, clean):
            return msg
    m = re.match(r"\s*use\s+`?(\w+)", clean)
    if m and m.group(1) != C.LAB_DB_NAME.lower():
        return "You can only use the sandbox database. It is already selected for you."
    return None


def danger_warning(stmt):
    clean = strip_literals(stmt).lower().strip()
    if re.match(r"(drop|truncate)\b", clean):
        return "This permanently removes a table or all of its rows: " + stmt[:60]
    if re.match(r"(delete|update)\b", clean) and not re.search(r"\bwhere\b", clean):
        return "This UPDATE/DELETE has no WHERE, so it changes EVERY row: " + stmt[:60]
    return None


def jsonable(v):
    if v is None or isinstance(v, (int, float, str)):
        return v
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", "replace")
    return str(v)  # Decimal, date, datetime, timedelta ...


def _rows_result(cur_description, rows, ms, sql):
    shown = rows[: C.MAX_ROWS]
    return {"type": "rows", "sql": sql, "columns": [d[0] for d in cur_description],
            "rows": [[jsonable(v) for v in r] for r in shown],
            "row_count": len(rows), "truncated": len(rows) > C.MAX_ROWS, "ms": ms}


def run_script(sql, confirm=False, trusted=False):
    """Run one or more statements on ONE connection (so transactions work).
    trusted=True is only used for our own check queries, never for learner text."""
    sql = (sql or "").strip()
    if not sql:
        return {"ok": False, "error": {"message": "The editor is empty. Type a query first."}}
    is_routine = bool(ROUTINE_RE.match(strip_literals(sql)))
    stmts = [sql.rstrip(";").strip()] if is_routine else split_statements(sql)
    if not stmts:
        return {"ok": False, "error": {"message": "No SQL found (only comments?)."}}
    if len(stmts) > C.MAX_STATEMENTS:
        return {"ok": False, "error": {"message": f"Too many statements (max {C.MAX_STATEMENTS})."}}
    if not trusted:
        for s in stmts:
            msg = check_forbidden(s)
            if msg:
                return {"ok": False, "blocked": True, "error": {"message": msg}}
        warnings = [w for w in map(danger_warning, stmts) if w]
        if warnings and not confirm:
            return {"ok": False, "needs_confirm": True, "warnings": warnings}

    results, t_all = [], time.perf_counter()
    conn = lab_conn()
    cur = conn.cursor(buffered=True)
    try:
        cur.execute(f"SET SESSION max_execution_time = {int(C.QUERY_TIMEOUT_MS)}")
        for s in stmts:
            t0 = time.perf_counter()
            try:
                call = CALL_RE.match(s)
                if call:  # stored procedure: needs callproc in mysql-connector
                    args = ast.literal_eval("(" + call.group(2) + ",)") if call.group(2).strip() else ()
                    cur.callproc(call.group(1), args)
                    ms = round((time.perf_counter() - t0) * 1000, 1)
                    sets = list(cur.stored_results())
                    for rs in sets:
                        results.append(_rows_result(rs.description, rs.fetchall(), ms, s))
                    if not sets:
                        results.append({"type": "ok", "sql": s, "affected": 0, "ms": ms})
                    continue
                cur.execute(s)
                ms = round((time.perf_counter() - t0) * 1000, 1)
                if cur.with_rows:
                    results.append(_rows_result(cur.description, cur.fetchall(), ms, s))
                else:
                    results.append({"type": "ok", "sql": s, "affected": max(0, cur.rowcount), "ms": ms})
            except (Error, ValueError, SyntaxError) as e:
                errno = getattr(e, "errno", None)
                msg = getattr(e, "msg", None) or str(e)
                results.append({"type": "error", "sql": s, "errno": errno, "message": msg,
                                "explanation": explain_error(errno, msg, s)})
                break  # stop at the first error, like the mysql client does
    finally:
        try: cur.close()
        finally: conn.close()   # an unfinished transaction is rolled back here
    ok = not any(r["type"] == "error" for r in results)
    return {"ok": ok, "results": results, "elapsed_ms": round((time.perf_counter() - t_all) * 1000, 1)}


# ---------- sandbox management ----------
def _s(x):
    return x.decode() if isinstance(x, (bytes, bytearray)) else str(x)


def load_scenario(name):
    """Wipe the sandbox and rebuild it from database/scenarios/<name>.sql."""
    if name not in SCENARIOS:
        raise ValueError("Unknown scenario")
    conn = lab_conn()
    cur = conn.cursor(buffered=True)
    try:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        cur.execute("SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = DATABASE()")
        for n, t in cur.fetchall():
            cur.execute(f"DROP {'VIEW' if 'VIEW' in _s(t) else 'TABLE'} IF EXISTS `{_s(n)}`")
        cur.execute("SELECT routine_name, routine_type FROM information_schema.routines WHERE routine_schema = DATABASE()")
        for n, t in cur.fetchall():
            cur.execute(f"DROP {_s(t)} IF EXISTS `{_s(n)}`")
        for stmt in split_statements((SCENARIO_DIR / f"{name}.sql").read_text(encoding="utf-8")):
            cur.execute(stmt)
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    finally:
        conn.close()
    from services.progress_tracker import set_setting
    set_setting("scenario", name)


def current_scenario():
    from services.progress_tracker import setting
    return setting("scenario", "school")


def ensure_scenario(name):
    if name and name != current_scenario():
        load_scenario(name)


def describe_lab():
    """Tables, columns, keys and foreign keys of the sandbox (used by Explorer and ER diagrams)."""
    conn = lab_conn()
    cur = conn.cursor(dictionary=True, buffered=True)
    try:
        cur.execute("""SELECT table_name AS t, column_name AS c, column_type AS ty, is_nullable AS nl,
                       column_key AS k, extra AS ex FROM information_schema.columns
                       WHERE table_schema = DATABASE() ORDER BY table_name, ordinal_position""")
        cols = cur.fetchall()
        cur.execute("""SELECT table_name AS t, column_name AS c, referenced_table_name AS rt,
                       referenced_column_name AS rc FROM information_schema.key_column_usage
                       WHERE table_schema = DATABASE() AND referenced_table_name IS NOT NULL""")
        fks = cur.fetchall()
        tables = {}
        for r in cols:
            tables.setdefault(_s(r["t"]), {"name": _s(r["t"]), "columns": []})["columns"].append(
                {"name": _s(r["c"]), "type": _s(r["ty"]), "nullable": _s(r["nl"]) == "YES",
                 "key": _s(r["k"]), "extra": _s(r["ex"])})
        for name, t in tables.items():
            cur.execute(f"SELECT COUNT(*) AS n FROM `{name}`")
            t["rows"] = cur.fetchone()["n"]
        return {"tables": list(tables.values()),
                "fks": [{"table": _s(f["t"]), "column": _s(f["c"]), "ref_table": _s(f["rt"]), "ref_column": _s(f["rc"])} for f in fks]}
    finally:
        conn.close()
