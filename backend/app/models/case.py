from __future__ import annotations

import uuid

from sqlalchemy import Float, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Case(Base, TimestampMixin):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_cases_created_at", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    detected_case_type: Mapped[str] = mapped_column(String(32), nullable=False, default="unclear")
    urgency_level: Mapped[str] = mapped_column(String(32), nullable=False, default="moderate")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    structured_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    handoff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    artifacts = relationship("Artifact", back_populates="case", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="case", cascade="all, delete-orphan")
    recommended_actions = relationship(
        "RecommendedAction",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="RecommendedAction.priority",
    )

