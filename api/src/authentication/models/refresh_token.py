"""
SQLAlchemy model for the RefreshToken entity.

Maps to capstone_app.refresh_tokens table.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'schema': 'capstone_app'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('capstone_app.users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        status = "revoked" if self.revoked_at else "active"
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, status={status})>"

    def is_valid(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at < datetime.now(timezone.utc):
            return False
        return True
