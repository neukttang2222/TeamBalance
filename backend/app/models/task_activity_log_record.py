from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskActivityLogRecord(Base):
    __tablename__ = "task_activity_logs"
    __table_args__ = (
        Index("ix_task_activity_logs_task_id_created_at", "task_id", "created_at"),
        Index("ix_task_activity_logs_submission_id", "submission_id"),
        Index("ix_task_activity_logs_action_type", "action_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), nullable=False)
    submission_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_work_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_work_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    from_score_lock_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_score_lock_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
