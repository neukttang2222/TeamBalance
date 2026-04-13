from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskSubmissionRecord(Base):
    __tablename__ = "task_submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "version_no", name="uq_task_submissions_task_version"),
        Index("ix_task_submissions_task_id_version_no", "task_id", "version_no"),
        Index("ix_task_submissions_task_id_evaluation_status", "task_id", "evaluation_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    submission_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    submission_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    provisional_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    question_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_retried_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
