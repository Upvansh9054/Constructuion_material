from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import BuyerCompanyType
from app.models.base import BaseMixin


class BuyerRecyclerProfile(Base, BaseMixin):
    """Module 11: Certified Buyers and Recyclers Directory."""
    __tablename__ = "buyer_recycler_profiles"

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    company_name = Column(String(255), nullable=False, index=True)
    company_type = Column(
        Enum(BuyerCompanyType),
        default=BuyerCompanyType.STEEL_MILL,
        nullable=False,
        index=True,
    )
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False)
    distance_km = Column(Float, default=25.0, nullable=False)

    accepted_categories = Column(JSON, default=list, nullable=False)  # ["STEEL", "CONCRETE"]
    certified_standards = Column(JSON, default=list, nullable=False)  # ["ISO 14001", "LEED"]
    total_purchased_tonnes = Column(Float, default=0.0, nullable=False)
    active_bids_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=4.8, nullable=False)

    contact_person = Column(String(150), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)

    # Relationships
    user = relationship("User", back_populates="buyer_profile")
