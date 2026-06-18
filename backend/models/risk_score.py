from datetime import datetime
from backend.extensions import db

class RiskScore(db.Model):
    __tablename__ = "risk_scores"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    risk_score    = db.Column(db.Integer)
    risk_level    = db.Column(db.String(20))
    calculated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }