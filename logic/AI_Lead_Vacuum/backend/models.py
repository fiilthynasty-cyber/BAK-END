"""SQLAlchemy ORM models + Pydantic v2 request/response schemas."""
from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.utils.db import Base


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class LeadORM(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    business_name: Mapped[str] = mapped_column(String(150), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    outreach_messages: Mapped[list[OutreachORM]] = relationship(
        "OutreachORM", back_populates="lead", cascade="all, delete-orphan"
    )


class OutreachORM(Base):
    __tablename__ = "outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lead_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    sent_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    lead: Mapped[LeadORM] = relationship("LeadORM", back_populates="outreach_messages")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class LeadBase(BaseModel):
    business_name: str = Field(min_length=1, max_length=150)
    url: str = Field(min_length=4, max_length=255)
    email: Optional[str] = Field(default=None, max_length=160)
    source: str = Field(default="manual", max_length=120)


class LeadCreate(LeadBase):
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    intent: Optional[str] = Field(default=None, max_length=50)
    ai_reason: Optional[str] = Field(default=None, max_length=4000)


class LeadUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    url: Optional[str] = Field(default=None, min_length=4, max_length=255)
    email: Optional[str] = Field(default=None, max_length=160)
    source: Optional[str] = Field(default=None, max_length=120)
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    intent: Optional[str] = Field(default=None, max_length=50)
    ai_reason: Optional[str] = Field(default=None, max_length=4000)


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score: float
    intent: Optional[str]
    ai_reason: Optional[str]
    created_at: datetime.datetime
    last_seen: datetime.datetime


class OutreachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    message: str
    status: str
    sent_at: datetime.datetime
