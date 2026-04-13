from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskBonusLogRecord(Base):
    __tablename__ = "task_bonus_logs"
    __table_args__ = (
        Index("ix_task_bonus_logs_task_id_created_at", "task_id", "created_at"),
        Index("ix_task_bonus_logs_submission_id", "submission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    submission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    version_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bonus_points: Mapped[float] = mapped_column(Float, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
