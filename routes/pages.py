"""HTML pages."""
import json
import datetime as dt
from flask import Blueprint, render_template, abort, redirect
from database.connection import query
from content.lessons import LESSONS, LEVELS, LEVEL_TITLES, LESSON_BY_SLUG, neighbors
from content.exercises import REGISTRY, ALL_TOPICS, TOPIC_CATEGORY, TOPIC_LESSON, public
from services import progress_tracker as pt
from services.sql_executor import SCENARIOS, current_scenario

pages = Blueprint("pages", __name__)


@pages.route("/")
def dashboard():
    return render_template("dashboard.html", s=pt.stats(LESSONS, LEVELS), level_titles=LEVEL_TITLES)


@pages.route("/learn")
@pages.route("/learn/<key>")
def learn(key=None):
    levels = {k: v for k, v in LEVELS.items() if key in (None, v["key"])}
    if not levels:
        abort(404)
    return render_template("lessons.html", levels=levels, lessons=LESSONS, done=pt.completed_slugs())


@pages.route("/lesson/<slug>")
def lesson_detail(slug):
    lesson = LESSON_BY_SLUG.get(slug) or abort(404)
    pt.visit_lesson(slug, lesson["title"])
    prev, nxt = neighbors(slug)
    status = query("SELECT * FROM lesson_progress WHERE slug=%s", (slug,), one=True)
    ex = public(REGISTRY["L:" + slug])
    return render_template("lesson_detail.html", l=lesson, prev=prev, next=nxt, status=status, ex=ex)


@pages.route("/playground")
def playground():
    return render_template("playground.html", scenarios=SCENARIOS, current=current_scenario())


@pages.route("/practice")
def practice():
    return render_template("practice.html", topics=ALL_TOPICS)


@pages.route("/exam")
def exam_setup():
    cats = {}
    for t in ALL_TOPICS:
        cats.setdefault(TOPIC_CATEGORY.get(t, "Other"), []).append(t)
    s = pt.stats(LESSONS, LEVELS)
    rec = 1 if s["answered"] < 5 else min(5, 1 + int(4 * s["correct"] / s["answered"]))
    history = query("SELECT * FROM exams WHERE status='done' ORDER BY id DESC LIMIT 10")
    for h in history:
        h["cfg"] = json.loads(h["config"])
    return render_template("exam_setup.html", cats=cats, rec=rec, history=history,
                           pass_percent=pt.setting("pass_percent", "70"))


@pages.route("/exam/<int:eid>")
def exam_take(eid):
    row = query("SELECT id, status FROM exams WHERE id=%s", (eid,), one=True) or abort(404)
    if row["status"] == "done":
        return redirect(f"/exam/{eid}/results")
    return render_template("exam.html", eid=eid)


@pages.route("/exam/<int:eid>/results")
def exam_results(eid):
    row = query("SELECT * FROM exams WHERE id=%s", (eid,), one=True) or abort(404)
    if row["status"] != "done":
        return redirect(f"/exam/{eid}")
    cfg, qids, ans = json.loads(row["config"]), json.loads(row["questions"]), json.loads(row["answers"])
    items, topics = [], {}
    for qid in qids:
        q, a = REGISTRY[qid], ans.get(qid)
        st = "skipped" if (not a or a.get("skipped")) else ("correct" if a["correct"] else "wrong")
        t = topics.setdefault(q["topic"], {"ok": 0, "n": 0})
        t["n"] += 1
        t["ok"] += st == "correct"
        items.append({"q": q, "a": a, "status": st,
                      "answer": q["options"][q["answer"]] if "options" in q else q.get("solution")})
    good = [k for k, v in topics.items() if v["ok"] / v["n"] >= 0.7]
    weak = [k for k, v in topics.items() if v["ok"] / v["n"] < 0.7]
    review = [LESSON_BY_SLUG[TOPIC_LESSON[t]] for t in weak if t in TOPIC_LESSON]
    counts = {k: sum(1 for i in items if i["status"] == k) for k in ("correct", "wrong", "skipped")}
    pct = round(100 * row["score"] / row["total"]) if row["total"] else 0
    return render_template("exam_results.html", e=row, cfg=cfg, items=items, topics=topics, good=good, weak=weak,
                           review=review, counts=counts, pct=pct)


@pages.route("/explorer")
def explorer():
    return render_template("database_explorer.html", scenarios=SCENARIOS, current=current_scenario())


@pages.route("/er")
def er():
    return render_template("er_diagrams.html", scenarios=SCENARIOS, current=current_scenario())


@pages.route("/progress")
def progress():
    s = pt.stats(LESSONS, LEVELS)
    study = {r["study_day"]: r["seconds"] for r in query("SELECT study_day, seconds FROM study_time WHERE study_day >= CURDATE() - INTERVAL 6 DAY")}
    week = [{"label": (dt.date.today() - dt.timedelta(days=i)).strftime("%a"),
             "min": round(study.get(dt.date.today() - dt.timedelta(days=i), 0) / 60)} for i in range(6, -1, -1)]
    exams = query("SELECT id, score, total, passed, finished_at FROM exams WHERE status='done' ORDER BY id DESC LIMIT 8")
    return render_template("progress.html", s=s, topics=pt.topic_stats(), week=week, exams=exams,
                           unfinished=pt.unfinished_exercises(), lessons=LESSONS, done=pt.completed_slugs())


@pages.route("/achievements")
def achievements():
    return render_template("achievements.html", items=pt.achievements_view())


@pages.route("/settings")
def settings():
    return render_template("settings.html", font=pt.setting("font_size", "14"), pass_percent=pt.setting("pass_percent", "70"),
                           scenarios=SCENARIOS, current=current_scenario())
