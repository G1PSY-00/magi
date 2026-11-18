"""Everything that is saved to MySQL: lessons, attempts, exams, time, streak, achievements."""
import datetime as dt
from database.connection import query, execute


def setting(k, default=None):
    row = query("SELECT v FROM settings WHERE k=%s", (k,), one=True)
    return row["v"] if row else default


def set_setting(k, v):
    execute("INSERT INTO settings (k, v) VALUES (%s, %s) ON DUPLICATE KEY UPDATE v = VALUES(v)", (k, str(v)))


def log(kind, detail=""):
    execute("INSERT INTO activity (kind, detail) VALUES (%s, %s)", (kind, detail[:200]))


def visit_lesson(slug, title):
    if not query("SELECT slug FROM lesson_progress WHERE slug=%s", (slug,), one=True):
        log("lesson", "Opened lesson: " + title)
    execute("INSERT INTO lesson_progress (slug, last_visit) VALUES (%s, NOW()) "
            "ON DUPLICATE KEY UPDATE last_visit = NOW()", (slug,))


def mark_lesson(slug, field, title):
    """field is 'exercise_done' or 'quiz_done'. A lesson is complete when both are done."""
    assert field in ("exercise_done", "quiz_done")
    execute(f"UPDATE lesson_progress SET {field}=1 WHERE slug=%s", (slug,))
    row = query("SELECT * FROM lesson_progress WHERE slug=%s", (slug,), one=True)
    if row and row["exercise_done"] and row["quiz_done"] and not row["completed_at"]:
        execute("UPDATE lesson_progress SET completed_at=NOW() WHERE slug=%s", (slug,))
        log("lesson_done", "Completed lesson: " + title)
        return True
    return False


def record_attempt(source, item_id, topic, correct):
    execute("INSERT INTO attempts (source, item_id, topic, correct) VALUES (%s,%s,%s,%s)",
            (source, item_id, topic, 1 if correct else 0))
    if correct and source == "practice":
        log("solved", f"Solved practice {item_id} ({topic})")


def heartbeat(seconds):
    seconds = max(0, min(int(seconds), 120))
    execute("INSERT INTO study_time (study_day, seconds) VALUES (CURDATE(), %s) "
            "ON DUPLICATE KEY UPDATE seconds = seconds + VALUES(seconds)", (seconds,))


def completed_slugs():
    return {r["slug"] for r in query("SELECT slug FROM lesson_progress WHERE completed_at IS NOT NULL")}


def streak():
    days = {r["d"] for r in query("SELECT DATE(created_at) AS d FROM activity UNION SELECT DATE(created_at) FROM attempts")}
    d = dt.date.today()
    if d not in days:
        d -= dt.timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= dt.timedelta(days=1)
    return n


def topic_stats():
    rows = query("SELECT topic, COUNT(*) AS n, SUM(correct) AS ok FROM attempts GROUP BY topic ORDER BY topic")
    return [{"topic": r["topic"], "n": int(r["n"]), "ok": int(r["ok"] or 0),
             "pct": round(100 * int(r["ok"] or 0) / int(r["n"]))} for r in rows]


def unfinished_exercises():
    rows = query("SELECT item_id, topic, COUNT(*) AS tries FROM attempts WHERE source IN ('practice','lesson') "
                 "GROUP BY item_id, topic HAVING SUM(correct)=0 ORDER BY MAX(created_at) DESC LIMIT 10")
    return rows


def stats(lessons, levels):
    done = completed_slugs()
    att = query("SELECT COUNT(*) AS n, COALESCE(SUM(correct),0) AS ok FROM attempts", one=True)
    ex = query("SELECT COUNT(*) AS n, COALESCE(AVG(100*score/total),0) AS avg_pct, COALESCE(MAX(100*score/total),0) AS best "
               "FROM exams WHERE status='done' AND total>0", one=True)
    secs = query("SELECT COALESCE(SUM(seconds),0) AS s FROM study_time", one=True)["s"]
    level_idx = 1
    for lv in sorted(levels):
        if any(l["slug"] not in done for l in lessons if l["level"] == lv):
            level_idx = lv
            break
        level_idx = lv
    nxt = next((l for l in lessons if l["slug"] not in done), None)
    last = query("SELECT slug FROM lesson_progress WHERE completed_at IS NULL ORDER BY last_visit DESC LIMIT 1", one=True)
    cont = next((l for l in lessons if last and l["slug"] == last["slug"]), nxt)
    return {
        "done": len(done), "total": len(lessons), "level": level_idx,
        "pct": round(100 * len(done) / len(lessons)) if lessons else 0,
        "streak": streak(), "answered": int(att["n"]), "correct": int(att["ok"]),
        "exams": int(ex["n"]), "exam_avg": round(float(ex["avg_pct"])), "exam_best": round(float(ex["best"])),
        "seconds": int(secs), "next": nxt, "continue": cont,
        "recent": query("SELECT kind, detail, created_at FROM activity WHERE kind <> 'run_ok' ORDER BY id DESC LIMIT 8"),
        "mastered": [t["topic"] for t in topic_stats() if t["n"] >= 3 and t["pct"] >= 80],
    }


# ---------- achievements ----------
def _count(sql, params=()):
    return int(query(sql, params, one=True)["n"])


ACHIEVEMENTS = [
    ("first_query", "First Query", "Run your first successful query in the editor.",
     lambda c: _count("SELECT COUNT(*) AS n FROM activity WHERE kind='run_ok'") >= 1),
    ("sql_beginner", "SQL Beginner", "Complete 5 lessons.", lambda c: len(c["done"]) >= 5),
    ("select_master", "SELECT Master", "Solve 8 SELECT / WHERE / ORDER BY exercises.",
     lambda c: _count("SELECT COUNT(*) AS n FROM attempts WHERE correct=1 AND topic IN ('SELECT','WHERE','ORDER BY')") >= 8),
    ("join_specialist", "JOIN Specialist", "Solve 4 JOIN exercises.",
     lambda c: _count("SELECT COUNT(*) AS n FROM attempts WHERE correct=1 AND topic='JOIN'") >= 4),
    ("database_architect", "Database Architect", "Complete every Advanced and Real-World lesson.",
     lambda c: all(l["slug"] in c["done"] for l in c["lessons"] if l["level"] >= 3)),
    ("query_expert", "Query Expert", "Pass an exam of 10+ questions with at least 80%.",
     lambda c: _count("SELECT COUNT(*) AS n FROM exams WHERE status='done' AND passed=1 AND total>=10 AND 100*score/total>=80") >= 1),
]


def check_achievements(lessons):
    ctx = {"done": completed_slugs(), "lessons": lessons}
    have = {r["code"] for r in query("SELECT code FROM achievements")}
    new = []
    for code, name, desc, rule in ACHIEVEMENTS:
        if code not in have and rule(ctx):
            execute("INSERT IGNORE INTO achievements (code) VALUES (%s)", (code,))
            log("achievement", "Unlocked: " + name)
            new.append(name)
    return new


def achievements_view():
    have = {r["code"]: r["unlocked_at"] for r in query("SELECT code, unlocked_at FROM achievements")}
    return [{"code": c, "name": n, "desc": d, "unlocked": c in have, "at": have.get(c)} for c, n, d, _ in ACHIEVEMENTS]


def reset_progress():
    for t in ("lesson_progress", "attempts", "activity", "study_time", "exams", "achievements"):
        execute(f"DELETE FROM {t}")
