from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_jwt_extended import create_access_token
from backend.models.user import User
from backend.models.risk_score import RiskScore
from backend.extensions import db
from backend.logger import log
from backend.risk_utils import score_to_level
from datetime import datetime
import dotenv, os, json

auth_bp = Blueprint("auth", __name__)

DEFAULT_NEW_ACCOUNT_SCORE = 50  # baseline risk score for brand-new, unverified accounts

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    session["login_time"] = int(datetime.now().timestamp())

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        log("error", f"Failed login for {email!r}")
        return jsonify({"error": "Invalid credentials."}), 401

    ADMIN_IDS = set(int(i) for i in json.loads(os.getenv("ADMIN_IDS")))
    is_admin  = int(user.id) in ADMIN_IDS

    token = create_access_token(identity=str(user.id))

    session["user_id"]  = user.id
    session["username"] = user.email.split("@")[0]
    if is_admin:
        session["is_admin"] = True

    log("info", f"User with id: '{user.id}' logged in successfully")

    return jsonify({
        "token":   token,
        "user_id": user.id,
        "email":   user.email,
    }), 200

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # NOTE: remove this block if a frontend call to /risk/calculate already
    # runs right after signup — otherwise new accounts have no RiskScore row
    # at all and the dashboard falls back to score=0 / level="UNKNOWN".
    baseline_entry = RiskScore(
        user_id    = user.id,
        risk_score = DEFAULT_NEW_ACCOUNT_SCORE,
        risk_level = score_to_level(DEFAULT_NEW_ACCOUNT_SCORE),
    )
    db.session.add(baseline_entry)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    session["user_id"]  = user.id
    session["username"] = user.email.split("@")[0]

    log("info", f"New user registered '{email!r}', id: '{user.id}'")

    return jsonify({
        "token":   token,
        "user_id": user.id,
        "email":   user.email,
    }), 201

@auth_bp.route("/admin_login", methods=["POST"])
def a_login():
    data = request.get_json()

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    session["login_time"] = int(datetime.now().timestamp())

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        log("error", f"Failed login for {email!r}")
        return jsonify({"error": "Invalid credentials."}), 401
    
    ADMIN_IDS = set(int(i) for i in json.loads(os.getenv("ADMIN_IDS")))

    session["user_id"]  = user.id
    session["username"] = user.email.split("@")[0]

    if int(user.id) in ADMIN_IDS:
        session["is_admin"] = True
    else:
        log("error", f"Non Admin login on admin for {user.id!r}")
        return jsonify({"error": "User not an Admin."}), 401

    token = create_access_token(identity=str(user.id))

    log("info", f"Admin with id: '{user.id}' logged in successfully")

    return jsonify({
        "token":   token,
        "user_id": user.id,
        "email":   user.email,
        "is_admin":   True,
    }), 200