from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import AuditAction
from app.models.base import BaseMixin


class AuditLog(Base, BaseMixin):
    """Module 15: Immutable Audit Logs for Regulatory and System Actions."""
    __tablename__ = "audit_logs"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(Enum(AuditAction), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(64), nullable=True, index=True)
    change_details = Column(JSON, nullable=True)

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

