from backend.extensions import db
from datetime import datetime


class Transaction(db.Model):
    __tablename__ = "transactions"

    id                  = db.Column(db.Integer, primary_key=True)
    sender_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount              = db.Column(db.Numeric(12, 2), nullable=False)
    status              = db.Column(db.String(20), nullable=False)   # success | failed | blocked
    reason              = db.Column(db.String(255), nullable=True)
    risk_score_at_time  = db.Column(db.Integer, nullable=True)
    risk_level_at_time  = db.Column(db.String(20), nullable=True)
    timestamp           = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":                  self.id,
            "sender_id":           self.sender_id,
            "recipient_id":        self.recipient_id,
            "amount":              float(self.amount),
            "status":              self.status,
            "reason":              self.reason,
            "risk_score_at_time":  self.risk_score_at_time,
            "risk_level_at_time":  self.risk_level_at_time,
            "timestamp":           self.timestamp.isoformat() if self.timestamp else None,
        }