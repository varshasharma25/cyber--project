from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from backend.models.verification_log import VerificationLog
from backend.extensions import db
from backend.logger import log

verify_bp = Blueprint("verify_bp", __name__)

def _log_attempt(user_id: int, method: str, status: str):
    entry = VerificationLog(
        user_id             = user_id,
        verification_method = method,
        status              = status,
    )
    db.session.add(entry)
    db.session.commit()

def _verified_token(user_id: int) -> str:
    """Issue a new JWT with verified=True claim."""
    return create_access_token(
        identity=str(user_id),
        additional_claims={"verified": True},
    )

@verify_bp.route("/sms", methods=["POST"])
@jwt_required()
def verify_sms():
    user_id = int(get_jwt_identity())
    code    = request.get_json().get("code", "").strip()

    if not code:
        return jsonify({"error": "Code is required."}), 400

    # it will accept "123456" for now
    if code != "123456":
        _log_attempt(user_id, "sms", "failed")
        log("error", f"SMS verification failed for user id: '{user_id}'")
        return jsonify({"error": "Invalid code."}), 401

    _log_attempt(user_id, "sms", "success")
    log("success", f"SMS verification successful for user id: '{user_id}'")

    return jsonify({
        "message": "SMS verification successful.",
        "token":   _verified_token(user_id),
    }), 200

@verify_bp.route("/2fa", methods=["POST"])
@jwt_required()
def verify_2fa():
    user_id = int(get_jwt_identity())
    code    = request.get_json().get("code", "").strip()

    if not code:
        return jsonify({"error": "Code is required."}), 400

    # it will accept "000000" for now
    if code != "000000":
        _log_attempt(user_id, "2fa", "failed")
        log("error", f"2FA verification failed for user: '{user_id}'")
        return jsonify({"error": "Invalid authenticator code."}), 401

    _log_attempt(user_id, "2fa", "success")
    log("success", f"2FA verification successful for user: '{user_id}'")

    return jsonify({
        "message": "2FA verification successful.",
        "token":   _verified_token(user_id),
    }), 200

@verify_bp.route("/biometric", methods=["POST"])
@jwt_required()
def verify_biometric():
    user_id = int(get_jwt_identity())
    data    = request.get_json()

    if not data:
        _log_attempt(user_id, "biometric", "failed")
        log("error", f"Biometric verification failed for user: '{user_id}'")
        return jsonify({"error": "No biometric data received."}), 400

    _log_attempt(user_id, "biometric", "success")
    log("success", f"Biometric verification successful for user: '{user_id}'")

    return jsonify({
        "message": "Biometric verification successful.",
        "token":   _verified_token(user_id),
    }), 200

@verify_bp.route("/status", methods=["GET"])
@jwt_required()
def status():
    user_id = int(get_jwt_identity())
    recent  = (
        VerificationLog.query
        .filter_by(user_id=user_id)
        .order_by(VerificationLog.timestamp.desc())
        .limit(10)
        .all()
    )
    return jsonify([e.to_dict() for e in recent]), 200