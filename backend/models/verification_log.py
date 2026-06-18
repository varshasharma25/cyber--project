from datetime import datetime
from backend.extensions import db


class VerificationLog(db.Model):
    __tablename__ = "verification_logs"

    id                   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id              = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    verification_method  = db.Column(db.String(50))
    status               = db.Column(db.String(20))
    timestamp            = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "verification_method": self.verification_method,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }