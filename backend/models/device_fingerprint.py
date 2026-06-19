# backend/models/device_fingerprint.py
from backend.extensions import db
from datetime import datetime

class DeviceFingerprint(db.Model):
    __tablename__ = "device_fingerprints"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fingerprint   = db.Column(db.String(64), nullable=False)  # sha256 hex digest
    first_seen_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "fingerprint": self.fingerprint,
            "first_seen_at": self.first_seen_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
        }