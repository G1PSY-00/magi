"""JSON endpoints used by the browser (run SQL, check answers, exams, progress)."""
import json
import random
from flask import Blueprint, jsonify, request, session
from database.connection import query, execute, is_connected
from content.lessons import LESSONS, LESSON_BY_SLUG
from content.exercises import REGISTRY, EXERCISES, public
from services import progress_tracker as pt
from services.sql_executor import run_script, ensure_scenario, load_scenario, current_scenario, describe_lab, SCENARIOS
from services.answer_validator import validate
from services.learning_assistant import why_wrong

api = Blueprint("api", __name__)


def body():
    return request.get_json(silent=True) or {}


def err(msg, code=400):
    return jsonify({"error": msg}), code


@api.get("/status")
def status():
    ok = is_connected()
    return jsonify({"mysql": ok, "scenario": current_scenario() if ok else None})


@api.post("/heartbeat")
def heartbeat():
    pt.heartbeat(body().get("seconds", 0))
    return jsonify({"ok": True})


# ---------- SQL editor ----------
@api.post("/run")
def run():
    d = body()
    if d.get("scenario") in SCENARIOS:
        ensure_scenario(d["scenario"])
    out = run_script(d.get("sql", ""), confirm=bool(d.get("confirm")))
    if out.get("ok"):
        pt.log("run_ok", "Ran a query")
        out["new_achievements"] = pt.check_achievements(LESSONS)
    return jsonify(out)


@api.post("/assistant")
def assistant():
    d = body()
    return jsonify({"messages": why_wrong(d.get("sql", ""), d.get("error"), d.get("feedback"))})


# ---------- sandbox / explorer ----------
@api.get("/schema")
def schema():
    sc = request.args.get("scenario")
    if sc in SCENARIOS:
        ensure_scenario(sc)
    data = describe_lab()
    data["scenario"] = current_scenario()
    data["scenario_name"] = SCENARIOS.get(data["scenario"], "")
    return jsonify(data)


@api.post("/scenario")
def scenario():
    d = body()
    if d.get("name") not in SCENARIOS:
        return err("Unknown scenario")
    if d.get("reset") or d["name"] != current_scenario():
        load_scenario(d["name"])
    return jsonify({"ok": True, "scenario": d["name"]})


@api.get("/table/<name>")
def table_preview(name):
    if name not in [t["name"] for t in describe_lab()["tables"]]:
        return err("Unknown table", 404)
    return jsonify(run_script(f"SELECT * FROM `{name}` LIMIT 50", trusted=True))


# ---------- lessons / exercises ----------
@api.post("/lesson/<slug>/quiz")
def lesson_quiz(slug):
    lesson = LESSON_BY_SLUG.get(slug)
    if not lesson:
        return err("Unknown lesson", 404)
    q = lesson["quiz"]
    correct = body().get("choice") == q["answer"]
    pt.record_attempt("quiz", slug, lesson["topic"], correct)
    done = pt.mark_lesson(slug, "quiz_done", lesson["title"]) if correct else False
    return jsonify({"correct": correct, "explain": q["explain"], "completed": done,
                    "new_achievements": pt.check_achievements(LESSONS)})


@api.post("/exercise/<eid>/submit")
def exercise_submit(eid):
    q = REGISTRY.get(eid)
    if not q or "solution" not in q:
        return err("Unknown exercise", 404)
    session["tried"] = list(set(session.get("tried", [])) | {eid})
    v = validate(q, body().get("sql", ""))
    is_lesson = eid.startswith("L:")
    pt.record_attempt("lesson" if is_lesson else "practice", eid, q["topic"], v["correct"])
    if v["correct"]:
        v["explanation"] = q["explanation"]
        if is_lesson:
            lesson = LESSON_BY_SLUG[q["lesson"]]
            v["lesson_completed"] = pt.mark_lesson(lesson["slug"], "exercise_done", lesson["title"])
    v["new_achievements"] = pt.check_achievements(LESSONS)
    return jsonify(v)


@api.get("/exercise/<eid>/hint")
def exercise_hint(eid):
    q = REGISTRY.get(eid)
    if not q:
        return err("Unknown exercise", 404)
    hints, n = q.get("hints", []), request.args.get("n", 0, type=int)
    return jsonify({"hint": hints[n] if n < len(hints) else "No more hints. Try 'WHY IS THIS WRONG?' or re-read the lesson.",
                    "more": n + 1 < len(hints)})


@api.get("/exercise/<eid>/solution")
def exercise_solution(eid):
    q = REGISTRY.get(eid)
    if not q or "solution" not in q:
        return err("Unknown exercise", 404)
    if eid not in session.get("tried", []):
        return err("Submit at least one attempt before viewing the solution.", 403)
    return jsonify({"solution": q["solution"], "explanation": q["explanation"]})


@api.get("/practice/new")
def practice_new():
    topic, level = request.args.get("topic", "all"), request.args.get("level", "all")
    exclude = set(request.args.get("exclude", "").split(","))
    pool = [q for q in EXERCISES if (topic == "all" or q["topic"] == topic) and (level == "all" or q["level"] == int(level))]
    fresh = [q for q in pool if q["id"] not in exclude] or pool
    if not fresh:
        return err("No exercises match this topic and difficulty. Try another combination.", 404)
    return jsonify(public(random.choice(fresh)))


# ---------- exams ----------
def load_exam(eid):
    row = query("SELECT *, TIMESTAMPDIFF(SECOND, started_at, NOW()) AS elapsed FROM exams WHERE id=%s", (eid,), one=True)
    if row:
        row["cfg"], row["qids"], row["ans"] = json.loads(row["config"]), json.loads(row["questions"]), json.loads(row["answers"])
    return row


@api.post("/exam/start")
def exam_start():
    d = body()
    topics, level, types = d.get("topics") or [], str(d.get("level", "mixed")), d.get("types") or ["mixed"]
    try:
        count = max(1, min(int(d.get("count", 10)), 60))
    except (TypeError, ValueError):
        return err("Number of questions must be a number.")
    if not topics:
        return err("Select at least one topic.")
    pool = [q for q in REGISTRY.values() if not q["id"].startswith("L:") and q["topic"] in topics]
    if level != "mixed":
        pool = [q for q in pool if q["level"] == int(level)]
    if "mixed" not in types:
        pool = [q for q in pool if q["type"] in types]
    if not pool:
        return err("No questions match this combination of topics, difficulty and type. Broaden your selection.")
    chosen = random.sample(pool, min(count, len(pool)))
    if level == "mixed":
        chosen.sort(key=lambda q: q["level"])          # difficulty rises gradually
    elif not d.get("randomize", True):
        chosen.sort(key=lambda q: q["id"])
    cfg = {"topics": topics, "level": level, "types": types, "count": count, "timer_minutes": int(d.get("timer_minutes") or 0),
           "pass_percent": max(1, min(int(d.get("pass_percent") or 70), 100)), "feedback": d.get("feedback", "final"),
           "randomize": bool(d.get("randomize", True))}
    eid = execute("INSERT INTO exams (config, questions, answers, total) VALUES (%s,%s,%s,%s)",
                  (json.dumps(cfg), json.dumps([q["id"] for q in chosen]), "{}", len(chosen)))
    pt.log("exam", f"Started exam with {len(chosen)} questions")
    warn = f"Only {len(chosen)} questions matched your selection (you asked for {count})." if len(chosen) < count else ""
    return jsonify({"id": eid, "warning": warn})


@api.get("/exam/<int:eid>")
def exam_get(eid):
    e = load_exam(eid)
    if not e:
        return err("Exam not found", 404)
    return jsonify({"config": e["cfg"], "status": e["status"], "elapsed": int(e["elapsed"]), "answers": e["ans"],
                    "questions": [public(REGISTRY[i]) for i in e["qids"]]})


@api.post("/exam/<int:eid>/answer")
def exam_answer(eid):
    e = load_exam(eid)
    d = body()
    q = REGISTRY.get(d.get("qid"))
    if not e or e["status"] != "active" or not q or q["id"] not in e["qids"]:
        return err("Invalid exam or question")
    if q["id"] in e["ans"]:
        return jsonify(e["ans"][q["id"]])
    res = {"skipped": False, "message": ""}
    if d.get("skip"):
        res.update(skipped=True, correct=False)
    elif "options" in q:
        res["correct"] = d.get("choice") == q["answer"]
    else:
        v = validate(q, d.get("sql", ""))
        res.update(correct=v["correct"], message=v["message"])
    e["ans"][q["id"]] = res
    execute("UPDATE exams SET answers=%s WHERE id=%s", (json.dumps(e["ans"]), eid))
    if not res["skipped"]:
        pt.record_attempt("exam", q["id"], q["topic"], res["correct"])
    out = {"saved": True, "skipped": res["skipped"]}
    if e["cfg"]["feedback"] == "immediate" and not res["skipped"]:
        out.update(correct=res["correct"], message=res["message"], explanation=q["explanation"],
                   answer=q["options"][q["answer"]] if "options" in q else q["solution"])
    return jsonify(out)


@api.post("/exam/<int:eid>/finish")
def exam_finish(eid):
    e = load_exam(eid)
    if not e:
        return err("Exam not found", 404)
    if e["status"] == "active":
        score = sum(1 for a in e["ans"].values() if a.get("correct"))
        total = len(e["qids"])
        passed = 1 if total and 100 * score / total >= e["cfg"]["pass_percent"] else 0
        execute("UPDATE exams SET status='done', score=%s, total=%s, passed=%s, finished_at=NOW(), "
                "seconds=TIMESTAMPDIFF(SECOND, started_at, NOW()) WHERE id=%s", (score, total, passed, eid))
        pt.log("exam_done", f"Finished exam: {score}/{total}")
        pt.check_achievements(LESSONS)
    return jsonify({"redirect": f"/exam/{eid}/results"})


# ---------- settings / progress ----------
@api.post("/settings")
def settings():
    d = body()
    try:
        pt.set_setting("font_size", max(10, min(int(d.get("font_size", 14)), 22)))
        pt.set_setting("pass_percent", max(1, min(int(d.get("pass_percent", 70)), 100)))
    except (TypeError, ValueError):
        return err("Settings must be numbers.")
    return jsonify({"ok": True})


@api.post("/progress/reset")
def progress_reset():
    if body().get("confirm") != "RESET":
        return err("Type RESET to confirm.")
    pt.reset_progress()
    return jsonify({"ok": True})
