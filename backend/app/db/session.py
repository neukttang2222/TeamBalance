from contextlib import contextmanager
from functools import lru_cache
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.models.auth_session_record import AuthSessionRecord
from app.models.project_member_record import ProjectMemberRecord
from app.models.project_record import ProjectRecord
from app.models.task_activity_log_record import TaskActivityLogRecord
from app.models.task_bonus_log_record import TaskBonusLogRecord
from app.models.task_record import TaskRecord
from app.models.task_submission_record import TaskSubmissionRecord
from app.models.team_member_record import TeamMemberRecord
from app.models.team_record import TeamRecord
from app.models.user_profile_record import UserProfileRecord


_db_initialized = False


@lru_cache
def get_engine():
    settings = get_settings()
    db_url = settings.supabase_db_url
    print("[db] engine init")
    print("[db] raw url prefix:", db_url.split("@")[0][:80])
    return create_engine(db_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def init_db() -> None:
    global _db_initialized

    if _db_initialized:
        return

    # Canonical shared/staging/production schema changes should be applied through
    # migration SQL. Runtime schema init stays as a local/dev MVP safety net.
    if not get_settings().enable_runtime_schema_init:
        _db_initialized = True
        return

    Base.metadata.create_all(
        bind=get_engine(),
        tables=[
            TaskRecord.__table__,
            TaskSubmissionRecord.__table__,
            TaskBonusLogRecord.__table__,
            TaskActivityLogRecord.__table__,
            TeamRecord.__table__,
            TeamMemberRecord.__table__,
            ProjectRecord.__table__,
            ProjectMemberRecord.__table__,
            UserProfileRecord.__table__,
            AuthSessionRecord.__table__,
        ],
    )
    _ensure_task_columns()
    _ensure_user_profile_columns()
    _ensure_supporting_indexes()
    _db_initialized = True


def _ensure_task_columns() -> None:
    inspector = inspect(get_engine())
    columns = {column["name"] for column in inspector.get_columns("tasks")}
    statements = []

    if "user_id" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN user_id VARCHAR(255)")

    if "parent_task_id" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN parent_task_id VARCHAR(36)")

    if "user_name" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN user_name VARCHAR(255)")

    if "creator_user_id" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN creator_user_id VARCHAR(255)")

    if "work_status" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN work_status VARCHAR(32) DEFAULT 'IN_PROGRESS'")

    if "score_lock_status" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN score_lock_status VARCHAR(32) DEFAULT 'UNLOCKED'")

    if "base_points" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN base_points DOUBLE PRECISION DEFAULT 0")

    if "locked_main_score" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN locked_main_score DOUBLE PRECISION")

    if "total_delta_bonus" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN total_delta_bonus DOUBLE PRECISION DEFAULT 0")

    if "approved_version_no" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN approved_version_no INTEGER")

    if "approved_submission_id" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN approved_submission_id VARCHAR(36)")

    if "approved_by" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN approved_by VARCHAR(255)")

    if "approved_at" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN approved_at TIMESTAMP")

    if "closed_by" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN closed_by VARCHAR(255)")

    if "closed_at" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN closed_at TIMESTAMP")

    if "canceled_by" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN canceled_by VARCHAR(255)")

    if "canceled_at" not in columns:
        statements.append("ALTER TABLE tasks ADD COLUMN canceled_at TIMESTAMP")

    if not statements:
        return

    with get_engine().begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_user_profile_columns() -> None:
    inspector = inspect(get_engine())
    columns = {column["name"] for column in inspector.get_columns("user_profiles")}
    statements = []

    if "password_hash" not in columns:
        statements.append("ALTER TABLE user_profiles ADD COLUMN password_hash VARCHAR(512)")

    if not statements:
        return

    with get_engine().begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_supporting_indexes() -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_tasks_project_id_work_status ON tasks (project_id, work_status)",
        "CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id_version_no ON task_submissions (task_id, version_no)",
        "CREATE INDEX IF NOT EXISTS ix_task_submissions_task_id_evaluation_status ON task_submissions (task_id, evaluation_status)",
        "CREATE INDEX IF NOT EXISTS ix_task_bonus_logs_task_id_created_at ON task_bonus_logs (task_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_task_activity_logs_task_id_created_at ON task_activity_logs (task_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_tasks_parent_task_id ON tasks (parent_task_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_user_profiles_email ON user_profiles (email)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_sessions_token_hash ON auth_sessions (token_hash)",
        "CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id)",
    ]
    with get_engine().begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@contextmanager
def get_db_session():
    init_db()
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
