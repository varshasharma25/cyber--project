from datetime import datetime
from backend.extensions import db

class BehaviorLog(db.Model):
    __tablename__ = "behavior_logs"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_type = db.Column(db.String(50))
    event_data = db.Column(db.JSON)
    timestamp  = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }