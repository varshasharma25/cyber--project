from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_jwt_extended import create_access_token
from backend.models.user import User
from backend.models.risk_score import RiskScore
from backend.extensions import db
from backend.logger import log
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    session["login_ts"] = int(datetime.now().timestamp())

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        log("error", f"Failed login for {email!r}")
        return jsonify({"error": "Invalid credentials."}), 401

    token = create_access_token(identity=str(user.id))

    session["user_id"]  = user.id
    session["username"] = user.email.split("@")[0]

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

    token = create_access_token(identity=str(user.id))

    session["user_id"]  = user.id
    session["username"] = user.email.split("@")[0]

    log("info", f"New user registered '{email!r}', id: '{user.id}'")

    return jsonify({
        "token":   token,
        "user_id": user.id,
        "email":   user.email,
    }), 201
