from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskRecord(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project_id_status", "project_id", "status"),
        Index("ix_tasks_project_id_work_status", "project_id", "work_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creator_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    task_goal: Mapped[str] = mapped_column(Text, nullable=False)
    task_weight: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    work_status: Mapped[str] = mapped_column(String(32), nullable=False, default="IN_PROGRESS")
    score_lock_status: Mapped[str] = mapped_column(String(32), nullable=False, default="UNLOCKED")
    base_points: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    locked_main_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_delta_bonus: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    approved_version_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_submission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weighted_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
