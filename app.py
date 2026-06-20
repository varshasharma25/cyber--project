from flask import Flask, render_template, redirect, json, url_for, session, jsonify, request as flask_request
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from functools import wraps
from backend.logger import read_logs
from backend.models.risk_score import RiskScore
from backend.models.verification_log import VerificationLog
from backend.models.user import User
from backend.models.transaction import Transaction

import os, sys, logging

from backend.extensions import db
from backend.logger import log, GREEN, RESET

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.logger.setLevel(logging.ERROR)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME')}"
    f"?ssl_verify_cert=false"
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
            return redirect(url_for("admin_dashboard"))
        return f(*args, **kwargs)
    return decorated

from backend.routes.auth        import auth_bp
from backend.routes.risk        import risk_bp
from backend.routes.verify      import verify_bp
from backend.routes.transaction import transaction_bp

app.register_blueprint(auth_bp,        url_prefix="/auth")
app.register_blueprint(risk_bp,        url_prefix="/risk")
app.register_blueprint(verify_bp,      url_prefix="/verify")
app.register_blueprint(transaction_bp, url_prefix="/transaction")


@app.route("/")
def login():
    if "user_id" in session:
        return redirect("/home")
    return render_template("login.html", title="Login", login_time=session.get("login_time", "—"))

@app.route("/signup")
def signup():
    if "user_id" in session:
        return redirect("/home")
    return render_template("signup.html", title="Sign Up")

@app.route("/home")
@require_login
def dashboard():

    latest_risk = (
        RiskScore.query
        .filter_by(user_id=session["user_id"])
        .order_by(RiskScore.calculated_at.desc())
        .first()
    )

    risk_score = latest_risk.risk_score if latest_risk else 0
    risk_level = latest_risk.risk_level.upper() if latest_risk else "UNKNOWN"

    trust_level = {
        "LOW": "HIGH",
        "MEDIUM": "MEDIUM",
        "HIGH": "LOW"
    }.get(risk_level, "UNKNOWN")

    latest_verification = (
        VerificationLog.query
        .filter_by(user_id=session["user_id"], status="success")
        .order_by(VerificationLog.timestamp.desc())
        .first()
    )

    if not latest_verification:
        verified = "-"
    else:
        risk_at_verification = (
            RiskScore.query
            .filter_by(user_id=session["user_id"])
            .filter(RiskScore.calculated_at <= latest_verification.timestamp)
            .order_by(RiskScore.calculated_at.desc())
            .first()
        )
        newer_risk = (
            RiskScore.query
            .filter_by(user_id=session["user_id"])
            .filter(RiskScore.calculated_at > latest_verification.timestamp)
            .order_by(RiskScore.calculated_at.asc())
            .first()
        )

        baseline_score = risk_at_verification.risk_score if risk_at_verification else 60  # DEFAULT_FALLBACK_SCORE

        if newer_risk and newer_risk.risk_score > baseline_score:
            verified = "PENDING"
        else:
            verified = "YES"

    session_count = (
        RiskScore.query
        .filter_by(user_id=session["user_id"])
        .count()
    )

    return render_template(
        "index.html",
        title="Home Page",
        risk_score=risk_score,
        session=session,
        trust_level=trust_level,
        session_count=session_count,
        verified=verified,
        ip=flask_request.remote_addr,
        risk_level=risk_level
    )

@app.route("/verify")
@require_login
def verify():
    method = flask_request.args.get("method", "sms")
    return render_template("verify.html", title="Verify", method=method)


@app.route("/admin_login")
def admin_login():
    if "user_id" in session:
        return redirect("/admin_dashboard")
    return render_template("admin.html", title="Admin Login", login_time=session.get("login_time", "—"))

@app.route("/admin/lookup")
@require_login
@require_admin
def admin_lookup():
    query = flask_request.args.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required."}), 400

    if query.isdigit():
        user = User.query.filter_by(id=int(query)).first()
    else:
        user = User.query.filter_by(email=query.lower()).first()

    if not user:
        return jsonify({"error": "User not found."}), 404

    risk_entries = (
        RiskScore.query
        .filter_by(user_id=user.id)
        .order_by(RiskScore.calculated_at.desc())
        .limit(20)
        .all()
    )

    verification_entries = (
        VerificationLog.query
        .filter_by(user_id=user.id)
        .order_by(VerificationLog.timestamp.desc())
        .limit(20)
        .all()
    )

    transaction_entries = (
        Transaction.query
        .filter(
            (Transaction.sender_id == user.id) |
            (Transaction.recipient_id == user.id)
        )
        .order_by(Transaction.timestamp.desc())
        .limit(20)
        .all()
    )

    return jsonify({
        "user": {
            "id":         user.id,
            "email":      user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "risk_history":         [r.to_dict() for r in risk_entries],
        "verification_history": [v.to_dict() for v in verification_entries],
        "transaction_history":  [t.to_dict() for t in transaction_entries],
    }), 200

@app.route("/admin_dashboard")
@require_login
@require_admin
def admin_dashboard():
    logs = read_logs()

    return render_template(
        "admin_dashboard.html",
        title="Admin Dashboard",
        session=session,
        recent_logs=logs[-10:]
    )

@app.route("/logs")
@require_login
@require_admin
def logs_page():
    entries = read_logs()
    return render_template("logs.html", title="Logs", logs=entries, session=session)

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    referrer = flask_request.referrer or ""

    came_from_admin = "/admin" in referrer

    if came_from_admin:
        log("info", f"Admin with id: '{user_id}' logged out successfully")
    else:
        log("info", f"User with id: '{user_id}' logged out successfully")

    session.clear()
    return redirect("/admin_login" if came_from_admin else "/")

if __name__ == "__main__":
    import flask.cli
    flask.cli.show_server_banner = lambda *_: None
    log("ready", f"{GREEN}Bob running at http://localhost:5000{RESET}")
    app.run(port=5000, debug=False)