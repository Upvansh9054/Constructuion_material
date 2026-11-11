from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.constants import ListingStatus
from app.models.base import BaseMixin


class MarketplaceListing(Base, BaseMixin):
    __tablename__ = "marketplace_listings"

    material_item_id = Column(
        String(36),
        ForeignKey("material_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seller_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    available_tonnes = Column(Float, nullable=False)
    min_order_tonnes = Column(Float, default=1.0, nullable=False)
    price_per_tonne_usd = Column(Float, nullable=False)
    total_price_usd = Column(Float, nullable=False)

    pickup_address = Column(String(500), nullable=False)
    pickup_city = Column(String(100), nullable=False, index=True)
    logistics_notes = Column(Text, nullable=True)

    status = Column(Enum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False, index=True)
    listed_at = Column(DateTime(timezone=True), nullable=True)
    sold_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    material_item = relationship("MaterialItem", back_populates="marketplace_listings")
    seller = relationship("User", back_populates="listings")

