"""MAGI SQL ACADEMY: run with  python app.py  then open http://127.0.0.1:5000"""
from flask import Flask, jsonify, render_template, request
from mysql.connector import Error as MySQLError
from config import Config
from content.lessons import LESSONS, LEVELS
from routes.pages import pages
from routes.api import api


def fmt_time(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(pages)
    app.register_blueprint(api, url_prefix="/api")
    app.jinja_env.filters["fmt_time"] = fmt_time

    @app.context_processor
    def sidebar_data():
        """Data every page needs: lesson tree, completed lessons and editor font size."""
        try:
            from services.progress_tracker import completed_slugs, setting
            done, font = completed_slugs(), setting("font_size", "14")
        except Exception:
            done, font = set(), "14"
        return {"NAV_LEVELS": LEVELS, "NAV_LESSONS": LESSONS, "NAV_DONE": done, "FONT_SIZE": font}

    @app.errorhandler(MySQLError)
    def db_error(e):
        if request.path.startswith("/api"):
            return jsonify({"error": "Database error: " + str(e)}), 503
        return render_template("error.html", message=str(e)), 503

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api"):
            return jsonify({"error": "Not found"}), 404
        return render_template("error.html", message="This sector does not exist.", code=404), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
