from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.behavior_log import BehaviorLog
from backend.models.risk_score import RiskScore
from backend.extensions import db
from backend.logger import log
from backend.risk_utils import score_to_level, level_to_verification

risk_bp = Blueprint("risk", __name__)


@risk_bp.route("/calculate", methods=["POST"])
@jwt_required()
def calculate():
    user_id  = int(get_jwt_identity())
    data     = request.get_json(silent=True) or {}
    behavior = data.get("behavior", {})

    if not behavior:
        return jsonify({"error": "No behavior data provided."}), 400

    log_entry = BehaviorLog(
        user_id    = user_id,
        event_type = behavior.get("event_type", "unknown"),
        event_data = behavior,
    )
    db.session.add(log_entry)
    db.session.flush()

    from backend.ml.risk_model import calculate_risk
    score = calculate_risk(user_id, behavior)
    level = score_to_level(score)
    required_verification = level_to_verification(level)

    risk_entry = RiskScore(
        user_id    = user_id,
        risk_score = score,
        risk_level = level,
    )
    db.session.add(risk_entry)
    db.session.commit()

    log("info", f"Risk calculated for user: '{user_id}', score:'{score}' and level: '{level}'")

    return jsonify({
        "risk_score":             score,
        "risk_level":             level,
        "required_verification":  required_verification,
    }), 200


@risk_bp.route("/history", methods=["GET"])
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    entries = (
        RiskScore.query
        .filter_by(user_id=user_id)
        .order_by(RiskScore.calculated_at.desc())
        .limit(20)
        .all()
    )
    return jsonify([e.to_dict() for e in entries]), 200