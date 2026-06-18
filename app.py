from flask import Flask, render_template, redirect, json, url_for, session, jsonify, request as flask_request
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from functools import wraps
from backend.logger import read_logs

import os, sys, logging

from backend.extensions import db
from backend.logger import log, GREEN, RESET

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

ADMIN_IDS=json.loads(os.getenv("ADMIN_IDS"))

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.logger.setLevel(logging.ERROR)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

ADMIN_IDS = set(int(i) for i in json.loads(os.getenv("ADMIN_IDS")))

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

@app.context_processor
def inject_permissions():
    uid = session.get("user_id")
    return {
        "is_admin": int(uid) in ADMIN_IDS if uid is not None else False,
        "admin_ids": ADMIN_IDS,
    }

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get("user_id")
        if uid is None or int(uid) not in ADMIN_IDS:
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

from backend.routes.auth   import auth_bp
from backend.routes.risk   import risk_bp
from backend.routes.verify import verify_bp

app.register_blueprint(auth_bp,   url_prefix="/auth")
app.register_blueprint(risk_bp,   url_prefix="/risk")
app.register_blueprint(verify_bp, url_prefix="/verify")

@app.route("/")
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html", title="Login", login_time=session.get("login_time", "—"))

@app.route("/home")
@require_login
def dashboard():
    return render_template("index.html", title="Home Page", session=session)

@app.route("/verify")
@require_login
def verify():
    method = flask_request.args.get("method", "sms")
    return render_template("verify.html", title="Verify", method=method)

@app.route("/logs")
@require_login
@require_admin
def logs_page():
    entries = read_logs()
    return render_template("logs.html", title="Logs", logs=entries, session=session)

@app.route("/logout")
def logout():
    log("info", f"User with id: '{session['user_id']}' logged out successfully")
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    import flask.cli
    flask.cli.show_server_banner = lambda *_: None
    log("ready", f"{GREEN}Bob running at http://localhost:5000{RESET}")
    app.run(port=5000, debug=False)