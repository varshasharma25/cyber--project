from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance       = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at    = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "email":      self.email,
            "balance":    float(self.balance) if self.balance is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }