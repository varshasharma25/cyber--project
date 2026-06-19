from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from backend.models.verification_log import VerificationLog
from backend.models.risk_score import RiskScore
from backend.extensions import db
from backend.logger import log
from backend.risk_utils import score_to_level

verify_bp = Blueprint("verify_bp", __name__)

DEFAULT_FALLBACK_SCORE = 60


def _log_attempt(user_id: int, method: str, status: str):
    entry = VerificationLog(
        user_id             = user_id,
        verification_method = method,
        status              = status,
    )
    db.session.add(entry)
    db.session.commit()

VERIFICATION_REDUCTION = {
    "sms":       20,
    "2fa":       25,
    "biometric": 25,
}

VERIFICATION_FLOOR = {
    "sms":       30,  # SMS can never bring score below "medium" threshold
    "2fa":       10,
    "biometric": 10,
}

VERIFICATION_PENALTY = {
    "sms":       15,
    "2fa":       20,
    "biometric": 30,  # failed biometric is the strongest signal of fraud
}

VERIFICATION_CEILING = {
    "sms":       100,
    "2fa":       100,
    "biometric": 100,
}


def _apply_verification_success(user_id: int, method: str):
    latest = (
        RiskScore.query
        .filter_by(user_id=user_id)
        .order_by(RiskScore.calculated_at.desc())
        .first()
    )

    current_score = latest.risk_score if latest else DEFAULT_FALLBACK_SCORE
    reduction      = VERIFICATION_REDUCTION.get(method, 0)
    floor          = VERIFICATION_FLOOR.get(method, 0)

    new_score = max(floor, current_score - reduction)
    new_level = score_to_level(new_score)

    entry = RiskScore(
        user_id    = user_id,
        risk_score = new_score,
        risk_level = new_level,
    )
    db.session.add(entry)
    db.session.commit()

    return new_score, new_level


def _apply_verification_failure(user_id: int, method: str):
    latest = (
        RiskScore.query
        .filter_by(user_id=user_id)
        .order_by(RiskScore.calculated_at.desc())
        .first()
    )

    current_score = latest.risk_score if latest else DEFAULT_FALLBACK_SCORE
    penalty        = VERIFICATION_PENALTY.get(method, 0)
    ceiling        = VERIFICATION_CEILING.get(method, 100)

    new_score = min(ceiling, current_score + penalty)
    new_level = score_to_level(new_score)

    entry = RiskScore(
        user_id    = user_id,
        risk_score = new_score,
        risk_level = new_level,
    )
    db.session.add(entry)
    db.session.commit()

    return new_score, new_level


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
        new_score, new_level = _apply_verification_failure(user_id, "sms")
        log("error", f"SMS verification failed for user id: '{user_id}', new score: '{new_score}', new level: '{new_level}'")
        return jsonify({
            "error":      "Invalid code.",
            "risk_score": new_score,
            "risk_level": new_level,
        }), 401

    _log_attempt(user_id, "sms", "success")
    new_score, new_level = _apply_verification_success(user_id, "sms")
    log("success", f"SMS verification successful for user id: '{user_id}', new score: '{new_score}', new level: '{new_level}'")

    return jsonify({
        "message":    "SMS verification successful.",
        "token":      _verified_token(user_id),
        "risk_score": new_score,
        "risk_level": new_level,
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
        new_score, new_level = _apply_verification_failure(user_id, "2fa")
        log("error", f"2FA verification failed for user: '{user_id}', new score: '{new_score}', new level: '{new_level}'")
        return jsonify({
            "error":      "Invalid authenticator code.",
            "risk_score": new_score,
            "risk_level": new_level,
        }), 401

    _log_attempt(user_id, "2fa", "success")
    new_score, new_level = _apply_verification_success(user_id, "2fa")
    log("success", f"2FA verification successful for user: '{user_id}', new score: '{new_score}', new level: '{new_level}'")

    return jsonify({
        "message":    "2FA verification successful.",
        "token":      _verified_token(user_id),
        "risk_score": new_score,
        "risk_level": new_level,
    }), 200


@verify_bp.route("/biometric", methods=["POST"])
@jwt_required()
def verify_biometric():
    user_id = int(get_jwt_identity())
    data    = request.get_json()

    if not data:
        _log_attempt(user_id, "biometric", "failed")
        new_score, new_level = _apply_verification_failure(user_id, "biometric")
        log("error", f"Biometric verification failed for user: '{user_id}', new score: '{new_score}', new level: '{new_level}'")
        return jsonify({
            "error":      "No biometric data received.",
            "risk_score": new_score,
            "risk_level": new_level,
        }), 400

    _log_attempt(user_id, "biometric", "success")
    new_score, new_level = _apply_verification_success(user_id, "biometric")
    log("success", f"Biometric verification successful for user: '{user_id}', new score: '{new_score}', new level: '{new_level}'")

    return jsonify({
        "message":    "Biometric verification successful.",
        "token":      _verified_token(user_id),
        "risk_score": new_score,
        "risk_level": new_level,
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