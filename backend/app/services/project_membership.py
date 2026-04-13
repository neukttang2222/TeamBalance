from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProjectMemberRecord, ProjectRecord, ProjectRole


SENSITIVE_REVIEW_ROLES = {ProjectRole.OWNER.value, ProjectRole.MANAGER.value}
TASK_CREATE_ROLES = {ProjectRole.OWNER.value, ProjectRole.MANAGER.value}


def get_project_or_404(session: Session, project_id: str) -> ProjectRecord:
    project = session.get(ProjectRecord, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")
    return project


def get_project_member(session: Session, project_id: str, user_id: str) -> ProjectMemberRecord | None:
    stmt = select(ProjectMemberRecord).where(
        ProjectMemberRecord.project_id == project_id,
        ProjectMemberRecord.user_id == user_id,
    )
    return session.execute(stmt).scalars().first()


def require_project_member(session: Session, project_id: str, user_id: str) -> ProjectMemberRecord:
    member = get_project_member(session, project_id, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="project membership required")
    return member


def require_sensitive_review_access(session: Session, project_id: str, user_id: str) -> ProjectMemberRecord:
    member = require_project_member(session, project_id, user_id)
    if member.role not in SENSITIVE_REVIEW_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="manager or owner role required")
    return member


def require_task_create_access(session: Session, project_id: str, user_id: str) -> ProjectMemberRecord:
    member = require_project_member(session, project_id, user_id)
    if member.role not in TASK_CREATE_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner or manager role required")
    return member


def is_sensitive_review_role(role: str) -> bool:
    return role in SENSITIVE_REVIEW_ROLES
