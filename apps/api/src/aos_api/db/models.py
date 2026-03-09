import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    public_key = Column(String(64), unique=True, nullable=False, index=True)
    secret_key = Column(String(64), unique=True, nullable=False)
    allowed_origins = Column(ARRAY(Text), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    slots = relationship("Slot", back_populates="tenant", cascade="all, delete-orphan")


class Slot(Base):
    __tablename__ = "slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    slot_key = Column(String(64), nullable=False)  # e.g. "hero-headline"
    selector = Column(Text, nullable=False)  # CSS selector
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant = relationship("Tenant", back_populates="slots")
    variations = relationship("Variation", back_populates="slot", cascade="all, delete-orphan")


class Variation(Base):
    __tablename__ = "variations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("slots.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g. "Bold Aesthetic"
    vibe_segment = Column(String(64), nullable=False)  # e.g. "bold"
    content_json = Column(JSONB, nullable=False)  # VariationContent
    is_control = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    slot = relationship("Slot", back_populates="variations")
    mab_state = relationship("MabState", back_populates="variation", uselist=False)


class MabState(Base):
    __tablename__ = "mab_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variation_id = Column(
        UUID(as_uuid=True), ForeignKey("variations.id"), unique=True, nullable=False
    )
    alpha = Column(Float, default=1.0, nullable=False)  # Beta dist successes + 1
    beta = Column(Float, default=1.0, nullable=False)  # Beta dist failures + 1
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    variation = relationship("Variation", back_populates="mab_state")


class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    session_id = Column(String(64), nullable=False)
    variation_id = Column(UUID(as_uuid=True), ForeignKey("variations.id"), nullable=True)
    slot_id = Column(String(64), nullable=True)
    event_type = Column(String(32), nullable=False)  # impression, click, conversion, etc.
    event_name = Column(String(128), nullable=True)
    referrer = Column(Text, nullable=True)
    utm_source = Column(String(128), nullable=True)
    vibe_segment = Column(String(64), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_events_variation_type", "variation_id", "event_type"),
        Index("ix_events_session", "session_id"),
    )
