from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for

from backend.extensions import db
from backend.models.user import User
from backend.models.risk_score import RiskScore
from backend.models.transaction import Transaction
from backend.logger import log

transaction_bp = Blueprint("transaction_bp", __name__)

# Risk levels that are not allowed to send money at all.
# risk_level is stored/compared lowercase ("low" / "medium" / "high").
BLOCKED_RISK_LEVELS = {"high"}


def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def _latest_risk(user_id):
    return (
        RiskScore.query
        .filter_by(user_id=user_id)
        .order_by(RiskScore.calculated_at.desc())
        .first()
    )


def _log_transaction(sender_id, recipient_id, amount, status, reason, risk_score, risk_level):
    entry = Transaction(
        sender_id          = sender_id,
        recipient_id       = recipient_id,
        amount             = amount,
        status             = status,
        reason             = reason,
        risk_score_at_time = risk_score,
        risk_level_at_time = risk_level,
    )
    db.session.add(entry)
    db.session.commit()
    return entry


@transaction_bp.route("/", methods=["GET"])
@require_login
def transaction_page():
    user = User.query.filter_by(id=session["user_id"]).first()
    balance = float(user.balance) if user and user.balance is not None else 0.0

    history = (
        Transaction.query
        .filter(
            (Transaction.sender_id == session["user_id"]) |
            (Transaction.recipient_id == session["user_id"])
        )
        .order_by(Transaction.timestamp.desc())
        .limit(20)
        .all()
    )

    latest_risk = _latest_risk(session["user_id"])
    risk_score = latest_risk.risk_score if latest_risk else 0
    risk_level = latest_risk.risk_level.upper() if latest_risk else "UNKNOWN"

    return render_template(
        "transaction.html",
        title="Transactions",
        balance=balance,
        history=[h.to_dict() for h in history],
        risk_score=risk_score,
        risk_level=risk_level,
        user_id=session["user_id"],
    )


@transaction_bp.route("/transfer", methods=["POST"])
@require_login
def transfer():
    user_id = session["user_id"]
    data = request.get_json() or {}

    recipient_query = str(data.get("recipient", "")).strip()
    amount_raw = data.get("amount")

    if not recipient_query or amount_raw is None:
        return jsonify({"error": "Recipient and amount are required."}), 400

    try:
        amount = Decimal(str(amount_raw))
    except InvalidOperation:
        return jsonify({"error": "Invalid amount."}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero."}), 400

    sender = User.query.filter_by(id=user_id).first()
    if not sender:
        return jsonify({"error": "Sender account not found."}), 404

    if recipient_query.isdigit():
        recipient = User.query.filter_by(id=int(recipient_query)).first()
    else:
        recipient = User.query.filter_by(email=recipient_query.lower()).first()

    if not recipient:
        return jsonify({"error": "Recipient not found."}), 404

    if recipient.id == sender.id:
        return jsonify({"error": "Cannot transfer to yourself."}), 400

    latest_risk = _latest_risk(user_id)
    risk_score  = latest_risk.risk_score if latest_risk else None
    risk_level  = latest_risk.risk_level.lower() if latest_risk else "unknown"

    # --- risk gate: block transfer if the sender's risk level is too high ---
    if risk_level in BLOCKED_RISK_LEVELS:
        _log_transaction(sender.id, recipient.id, amount, "blocked", "Risk level too high", risk_score, risk_level)
        log("error", f"Transfer blocked for user id: '{user_id}', risk level: '{risk_level}', risk score: '{risk_score}'")
        return jsonify({
            "error":      "Transfer blocked due to elevated risk level. Please re-verify your identity.",
            "risk_score": risk_score,
            "risk_level": risk_level,
        }), 403

    sender_balance = Decimal(str(sender.balance)) if sender.balance is not None else Decimal("0")

    if sender_balance < amount:
        _log_transaction(sender.id, recipient.id, amount, "failed", "Insufficient funds", risk_score, risk_level)
        log("error", f"Transfer failed for user id: '{user_id}', insufficient funds, balance: '{sender_balance}', requested: '{amount}'")
        return jsonify({"error": "Insufficient balance."}), 400

    recipient_balance = Decimal(str(recipient.balance)) if recipient.balance is not None else Decimal("0")

    sender.balance    = sender_balance - amount
    recipient.balance = recipient_balance + amount

    db.session.add(sender)
    db.session.add(recipient)
    db.session.commit()

    _log_transaction(sender.id, recipient.id, amount, "success", None, risk_score, risk_level)
    log("success", f"Transfer of '{amount}' from user id: '{user_id}' to user id: '{recipient.id}' successful, risk level: '{risk_level}', new sender balance: '{sender.balance}'")

    return jsonify({
        "message":     "Transfer successful.",
        "new_balance": float(sender.balance),
        "risk_score":  risk_score,
        "risk_level":  risk_level,
    }), 200


@transaction_bp.route("/history", methods=["GET"])
@require_login
def history():
    entries = (
        Transaction.query
        .filter(
            (Transaction.sender_id == session["user_id"]) |
            (Transaction.recipient_id == session["user_id"])
        )
        .order_by(Transaction.timestamp.desc())
        .limit(50)
        .all()
    )
    return jsonify([e.to_dict() for e in entries]), 200