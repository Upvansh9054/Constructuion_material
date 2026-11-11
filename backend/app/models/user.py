from sqlalchemy import Boolean, Column, Enum, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import UserRole
from app.models.base import BaseMixin


class User(Base, BaseMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CONTRACTOR, nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    sites = relationship("DemolitionSite", back_populates="contractor", cascade="all, delete-orphan")
    surveys = relationship("SiteSurvey", back_populates="surveyor")
    listings = relationship("MarketplaceListing", back_populates="seller", cascade="all, delete-orphan")
    buyer_profile = relationship("BuyerRecyclerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bids = relationship("EnquiryTransaction", back_populates="buyer", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
