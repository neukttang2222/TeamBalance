import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select

from app.db.session import get_db_session
from app.models import (
    ProjectMemberRecord,
    ProjectRecord,
    ProjectRole,
    ProjectTaskView,
    TaskActivityLogRecord,
    TaskBonusLogRecord,
    TaskRecord,
    TeamMemberRecord,
    TeamRecord,
    UserProfileRecord,
)
from app.schemas import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberAddRequest,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberUpdateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    ProjectTaskReadItemResponse,
    ProjectTaskReadListResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TeamCreateRequest,
    TeamListResponse,
    TeamMemberAddRequest,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberUpdateRequest,
    TeamResponse,
    TeamUpdateRequest,
)
from app.services.project_membership import (
    get_project_or_404,
    require_project_member,
    require_sensitive_review_access,
    require_task_create_access,
)
from app.services.auth_service import (
    find_existing_user_by_email,
    find_existing_user_by_id,
)
from app.services.task_service_phase1 import create_task


def create_team(payload: TeamCreateRequest, actor_user_id: str | None = None) -> TeamResponse:
    now = _now()
    created_by = actor_user_id or payload.created_by
    with get_db_session() as session:
        team = TeamRecord(
            id=str(uuid4()),
            name=payload.name,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        session.add(team)
        if created_by:
            _ensure_team_member(session, team.id, created_by, ProjectRole.OWNER.value, now)
        session.flush()
        return TeamResponse(
            team_id=team.id,
            name=team.name,
            created_by=team.created_by,
            current_user_role=ProjectRole.OWNER.value if created_by else None,
            created_at=team.created_at.isoformat(),
        )


def list_teams(user_id: str) -> TeamListResponse:
    with get_db_session() as session:
        stmt = (
            select(TeamRecord, TeamMemberRecord.team_role)
            .join(TeamMemberRecord, TeamMemberRecord.team_id == TeamRecord.id)
            .where(TeamMemberRecord.user_id == user_id)
            .order_by(TeamRecord.created_at.desc(), TeamRecord.id.desc())
        )
        rows = session.execute(stmt).all()
        return TeamListResponse(
            teams=[
                TeamResponse(
                    team_id=team.id,
                    name=team.name,
                    created_by=team.created_by,
                    current_user_role=role,
                    created_at=team.created_at.isoformat(),
                )
                for team, role in rows
            ]
        )


def update_team(team_id: str, payload: TeamUpdateRequest, actor_user_id: str) -> TeamResponse:
    with get_db_session() as session:
        team = _get_team_or_404(session, team_id)
        _require_team_manage_access(session, team_id, actor_user_id)
        team.name = payload.name
        team.updated_at = _now()
        session.flush()
        current_member = _get_team_member(session, team_id, actor_user_id)
        current_role = current_member.team_role if current_member is not None else None
        return TeamResponse(
            team_id=team.id,
            name=team.name,
            created_by=team.created_by,
            current_user_role=current_role,
            created_at=team.created_at.isoformat(),
        )


def delete_team(team_id: str, actor_user_id: str) -> TeamResponse:
    with get_db_session() as session:
        team = _get_team_or_404(session, team_id)
        _require_team_owner_access(session, team_id, actor_user_id)
        projects = session.execute(
            select(ProjectRecord).where(ProjectRecord.team_id == team_id)
        ).scalars().all()
        if projects:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="해당 팀에 프로젝트가 남아 있어 삭제할 수 없습니다.",
            )

        response = TeamResponse(
            team_id=team.id,
            name=team.name,
            created_by=team.created_by,
            current_user_role=ProjectRole.OWNER.value,
            created_at=team.created_at.isoformat(),
        )
        members = session.execute(
            select(TeamMemberRecord).where(TeamMemberRecord.team_id == team_id)
        ).scalars().all()
        for member in members:
            session.delete(member)
        session.delete(team)
        session.flush()
        return response


def list_team_members(team_id: str, actor_user_id: str) -> TeamMemberListResponse:
    with get_db_session() as session:
        _get_team_or_404(session, team_id)
        _require_team_member(session, team_id, actor_user_id)
        members = session.execute(
            select(TeamMemberRecord)
            .where(TeamMemberRecord.team_id == team_id)
            .order_by(TeamMemberRecord.team_role, TeamMemberRecord.user_id)
        ).scalars().all()
        return TeamMemberListResponse(
            team_id=team_id,
            members=[_team_member_response(member, session.get(UserProfileRecord, member.user_id)) for member in members],
        )


def add_team_member(team_id: str, payload: TeamMemberAddRequest, actor_user_id: str) -> TeamMemberResponse:
    now = _now()
    with get_db_session() as session:
        _get_team_or_404(session, team_id)
        actor = _require_team_manage_access(session, team_id, actor_user_id)
        if payload.role == ProjectRole.OWNER and actor.team_role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can grant owner role")

        if payload.email:
            user = find_existing_user_by_email(session, payload.email)
            target_user_id = user.id
        elif payload.user_id:
            user = find_existing_user_by_id(session, payload.user_id)
            target_user_id = user.id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="member email is required")

        member = _ensure_team_member(session, team_id, target_user_id, payload.role.value, now)
        session.flush()
        return _team_member_response(member, user)


def update_team_member(
    team_id: str,
    target_user_id: str,
    payload: TeamMemberUpdateRequest,
    actor_user_id: str,
) -> TeamMemberResponse:
    if actor_user_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="self role change is not allowed")

    with get_db_session() as session:
        _get_team_or_404(session, team_id)
        actor = _require_team_manage_access(session, team_id, actor_user_id)
        target = _require_team_member(session, team_id, target_user_id)

        if target.team_role == ProjectRole.OWNER.value and actor.team_role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can change owner role")
        if target.team_role == ProjectRole.OWNER.value and payload.role != ProjectRole.OWNER and _count_team_owners(session, team_id) <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot remove last owner role")
        if payload.role == ProjectRole.OWNER and actor.team_role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can grant owner role")

        target.team_role = payload.role.value
        session.flush()
        return _team_member_response(target, session.get(UserProfileRecord, target.user_id))


def remove_team_member(team_id: str, target_user_id: str, actor_user_id: str) -> TeamMemberResponse:
    if actor_user_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="self removal is not allowed")

    with get_db_session() as session:
        _get_team_or_404(session, team_id)
        actor = _require_team_manage_access(session, team_id, actor_user_id)
        target = _require_team_member(session, team_id, target_user_id)

        if target.team_role == ProjectRole.OWNER.value and actor.team_role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can remove owner")
        if target.team_role == ProjectRole.OWNER.value and _count_team_owners(session, team_id) <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot remove last owner")

        linked_projects = session.execute(
            select(ProjectRecord)
            .join(ProjectMemberRecord, ProjectRecord.id == ProjectMemberRecord.project_id)
            .where(
                ProjectRecord.team_id == team_id,
                ProjectMemberRecord.user_id == target_user_id,
            )
        ).scalars().all()
        if linked_projects:
            project_names = ", ".join(project.name for project in linked_projects[:3])
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This user is still a project member and cannot be removed from the team. Remove the project membership first. Projects: {project_names}",
            )

        response = _team_member_response(target, session.get(UserProfileRecord, target.user_id))
        session.delete(target)
        session.flush()
        return response


def create_project(team_id: str, payload: ProjectCreateRequest, actor_user_id: str | None = None) -> ProjectResponse:
    now = _now()
    created_by = actor_user_id or payload.created_by
    with get_db_session() as session:
        team = session.get(TeamRecord, team_id)
        if team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="team not found")

        project = ProjectRecord(
            id=str(uuid4()),
            team_id=team_id,
            name=payload.name,
            description=payload.description,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        session.add(project)

        if created_by:
            _ensure_team_member(session, team_id, created_by, ProjectRole.OWNER.value, now)
            _ensure_project_member(
                session=session,
                project_id=project.id,
                user_id=created_by,
                display_name=None,
                role=ProjectRole.OWNER.value,
                joined_at=now,
            )

        session.flush()
        return _project_response(project)


def list_team_projects(team_id: str, user_id: str) -> ProjectListResponse:
    with get_db_session() as session:
        team_member = session.execute(
            select(TeamMemberRecord).where(
                TeamMemberRecord.team_id == team_id,
                TeamMemberRecord.user_id == user_id,
            )
        ).scalars().first()
        if team_member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="team membership required")

        stmt = (
            select(ProjectRecord, ProjectMemberRecord.role)
            .join(ProjectMemberRecord, ProjectMemberRecord.project_id == ProjectRecord.id)
            .where(
                ProjectRecord.team_id == team_id,
                ProjectMemberRecord.user_id == user_id,
            )
            .order_by(ProjectRecord.created_at.desc(), ProjectRecord.id.desc())
        )
        rows = session.execute(stmt).all()
        return ProjectListResponse(
            team_id=team_id,
            projects=[_project_response(project, current_user_role=role) for project, role in rows],
        )


def update_project(project_id: str, payload: ProjectUpdateRequest, actor_user_id: str) -> ProjectResponse:
    with get_db_session() as session:
        project = get_project_or_404(session, project_id)
        member = require_sensitive_review_access(session, project_id, actor_user_id)
        if payload.team_id and payload.team_id != project.team_id:
            _get_team_or_404(session, payload.team_id)
            has_tasks = session.execute(
                select(TaskRecord).where(TaskRecord.project_id == project_id)
            ).scalars().first()
            if has_tasks is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="기존 task가 있는 프로젝트는 현재 단계에서 소속 팀을 변경할 수 없습니다.",
                )
            project.team_id = payload.team_id
        project.name = payload.name
        project.description = payload.description
        project.updated_at = _now()
        session.flush()
        return _project_response(project, current_user_role=member.role)


def delete_project(project_id: str, actor_user_id: str) -> ProjectResponse:
    with get_db_session() as session:
        project = get_project_or_404(session, project_id)
        member = require_sensitive_review_access(session, project_id, actor_user_id)
        tasks = session.execute(
            select(TaskRecord).where(TaskRecord.project_id == project_id)
        ).scalars().all()
        if tasks:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="해당 프로젝트에 task가 남아 있어 삭제할 수 없습니다.",
            )

        response = _project_response(project, current_user_role=member.role)
        members = session.execute(
            select(ProjectMemberRecord).where(ProjectMemberRecord.project_id == project_id)
        ).scalars().all()
        for project_member in members:
            session.delete(project_member)
        session.delete(project)
        session.flush()
        return response


def add_project_member(project_id: str, payload: ProjectMemberAddRequest) -> ProjectMemberResponse:
    now = _now()
    with get_db_session() as session:
        project = get_project_or_404(session, project_id)
        if payload.email:
            user = find_existing_user_by_email(session, payload.email)
            target_user_id = user.id
            display_name = payload.display_name or user.display_name
        elif payload.user_id:
            user = find_existing_user_by_id(session, payload.user_id)
            target_user_id = user.id
            display_name = payload.display_name or user.display_name
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="member email is required")
        existing_member = _get_project_member(session, project_id, target_user_id)
        if (
            existing_member is not None
            and existing_member.role in {ProjectRole.OWNER.value, ProjectRole.MANAGER.value}
            and payload.role == ProjectRole.MEMBER
            and _count_project_leads(session, project_id) <= 1
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="at least one owner or manager is required",
            )
        member = _ensure_project_member(
            session=session,
            project_id=project_id,
            user_id=target_user_id,
            display_name=display_name,
            role=payload.role.value,
            joined_at=now,
        )
        session.flush()
        return _project_member_response(member, user)


def update_project_member(
    project_id: str,
    target_user_id: str,
    payload: ProjectMemberUpdateRequest,
    actor_user_id: str,
) -> ProjectMemberResponse:
    if actor_user_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="self role change is not allowed")

    with get_db_session() as session:
        project = get_project_or_404(session, project_id)
        actor = require_sensitive_review_access(session, project_id, actor_user_id)
        target = require_project_member(session, project_id, target_user_id)

        if target.role == ProjectRole.OWNER.value and actor.role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can change owner role")
        if target.role == ProjectRole.OWNER.value and payload.role != ProjectRole.OWNER and _count_project_owners(session, project_id) <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot remove last owner role")
        if payload.role == ProjectRole.OWNER and actor.role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can grant owner role")

        target.role = payload.role.value
        if payload.display_name is not None:
            target.display_name = payload.display_name
        _ensure_team_member(session, project.team_id, target.user_id, target.role, target.joined_at)
        session.flush()
        return _project_member_response(target, session.get(UserProfileRecord, target.user_id))


def remove_project_member(project_id: str, target_user_id: str, actor_user_id: str) -> ProjectMemberResponse:
    if actor_user_id == target_user_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="self removal is not allowed")

    with get_db_session() as session:
        get_project_or_404(session, project_id)
        actor = require_sensitive_review_access(session, project_id, actor_user_id)
        target = require_project_member(session, project_id, target_user_id)

        if target.role == ProjectRole.OWNER.value and actor.role != ProjectRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only owner can remove owner")
        if target.role == ProjectRole.OWNER.value and _count_project_owners(session, project_id) <= 1:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cannot remove last owner")

        response = _project_member_response(target, session.get(UserProfileRecord, target.user_id))
        session.delete(target)
        session.flush()
        return response


def list_project_members(project_id: str, user_id: str | None = None) -> ProjectMemberListResponse:
    with get_db_session() as session:
        get_project_or_404(session, project_id)
        if user_id:
            require_project_member(session, project_id, user_id)

        stmt = select(ProjectMemberRecord).where(ProjectMemberRecord.project_id == project_id).order_by(
            ProjectMemberRecord.role,
            ProjectMemberRecord.user_id,
        )
        members = session.execute(stmt).scalars().all()
        return ProjectMemberListResponse(
            project_id=project_id,
            members=[_project_member_response(member, session.get(UserProfileRecord, member.user_id)) for member in members],
        )


def create_project_task(project_id: str, payload: TaskCreateRequest, actor_user_id: str | None = None) -> TaskCreateResponse:
    if actor_user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="actor_user_id is required")
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="task assignee is required")

    with get_db_session() as session:
        get_project_or_404(session, project_id)
        require_task_create_access(session, project_id, actor_user_id)
        assignee = require_project_member(session, project_id, payload.user_id)
        user_profile = session.get(UserProfileRecord, payload.user_id)
        assignee_name = (
            payload.user_name
            or assignee.display_name
            or (user_profile.display_name if user_profile else None)
            or (user_profile.email if user_profile else None)
            or payload.user_id
        )
        _validate_parent_task_project(session, project_id, payload.parent_task_id)

    normalized_payload = payload.model_copy(update={"project_id": project_id, "user_name": assignee_name})
    return create_task(normalized_payload, actor_user_id=actor_user_id)


def list_project_tasks_by_view(
    project_id: str,
    view: ProjectTaskView,
    user_id: str,
) -> ProjectTaskReadListResponse:
    with get_db_session() as session:
        get_project_or_404(session, project_id)
        if view == ProjectTaskView.SENSITIVE_REVIEW:
            require_sensitive_review_access(session, project_id, user_id)
        else:
            require_project_member(session, project_id, user_id)

        stmt = select(TaskRecord).where(TaskRecord.project_id == project_id)
        if view == ProjectTaskView.MY:
            stmt = stmt.where(TaskRecord.user_id == user_id)
        stmt = stmt.order_by(TaskRecord.created_at.desc(), TaskRecord.id.desc())

        task_records = session.execute(stmt).scalars().all()
        serializer = _get_task_view_serializer(view)
        tasks = [serializer(session, task_record) for task_record in task_records]

        return ProjectTaskReadListResponse(project_id=project_id, view=view.value, tasks=tasks)


def _serialize_overview_task(session, task_record: TaskRecord) -> ProjectTaskReadItemResponse:
    from app.services.task_service_phase1 import _get_latest_submission

    submission = _get_latest_submission(session, task_record.id)
    return ProjectTaskReadItemResponse(**_overview_payload(task_record, submission))


def _serialize_my_task(session, task_record: TaskRecord) -> ProjectTaskReadItemResponse:
    from app.services.task_service_phase1 import _get_latest_submission

    submission = _get_latest_submission(session, task_record.id)
    return ProjectTaskReadItemResponse(**_my_payload(session, task_record, submission))


def _serialize_sensitive_review_task(session, task_record: TaskRecord) -> ProjectTaskReadItemResponse:
    from app.services.task_service_phase1 import _get_latest_submission

    submission = _get_latest_submission(session, task_record.id)
    payload = _my_payload(session, task_record, submission)
    payload.update(
        {
            "ai_factor": submission.ai_factor if submission is not None else None,
            "provisional_score": submission.provisional_score if submission is not None else None,
            "locked_main_score": task_record.locked_main_score,
            "total_delta_bonus": task_record.total_delta_bonus,
            "failed_stage": submission.failed_stage if submission is not None else task_record.failed_stage,
            "error_message": submission.error_message if submission is not None else task_record.error_message,
            "bonus_logs": _bonus_log_payloads(session, task_record.id),
            "activity_logs": _activity_log_payloads(session, task_record.id),
        }
    )
    return ProjectTaskReadItemResponse(**payload)


def _overview_payload(task_record: TaskRecord, submission) -> dict:
    return {
        "task_id": task_record.id,
        "project_id": task_record.project_id,
        "parent_task_id": task_record.parent_task_id,
        "user_id": task_record.user_id,
        "user_name": task_record.user_name,
        "title": task_record.title,
        "task_type": task_record.task_type,
        "task_goal": task_record.task_goal,
        "task_weight": task_record.task_weight,
        "status": task_record.status,
        "work_status": task_record.work_status,
        "evaluation_status": submission.evaluation_status if submission is not None else task_record.status,
        "score_lock_status": task_record.score_lock_status,
        "has_submission": submission is not None,
        "current_submission_id": submission.id if submission is not None else None,
        "current_submission_version_no": submission.version_no if submission is not None else None,
        "submission_content": submission.submission_content if submission is not None else task_record.content,
        "submitted_at": submission.submitted_at.isoformat() if submission is not None else None,
        "approved_version_no": task_record.approved_version_no,
        "created_at": task_record.created_at.isoformat(),
        "updated_at": task_record.updated_at.isoformat(),
    }


def _is_task_approved(task_record: TaskRecord) -> bool:
    return bool(
        task_record.work_status == "APPROVED"
        or task_record.score_lock_status in {"LOCKED", "LOCKED_WITH_BONUS"}
        or task_record.approved_version_no
    )


def _get_final_score(task_record: TaskRecord) -> float | None:
    if not _is_task_approved(task_record):
        return None
    return float(task_record.locked_main_score or 0) + float(task_record.total_delta_bonus or 0)


def _my_payload(session, task_record: TaskRecord, submission) -> dict:
    payload = _overview_payload(task_record, submission)
    latest_review_feedback = _latest_review_feedback_payload(session, task_record.id)
    payload.update(
        {
            "ai_question": submission.ai_question if submission is not None else task_record.ai_question,
            "user_answer": submission.user_answer if submission is not None else task_record.user_answer,
            "raw_score": submission.raw_score if submission is not None else task_record.raw_score,
            "weighted_score": task_record.weighted_score,
            "ai_comment": submission.ai_comment if submission is not None else task_record.ai_comment,
            "final_score": _get_final_score(task_record),
            "locked_main_score": task_record.locked_main_score,
            "total_delta_bonus": task_record.total_delta_bonus,
            "latest_review_feedback_type": latest_review_feedback["type"],
            "latest_review_feedback_reason": latest_review_feedback["reason"],
            "latest_review_feedback_at": latest_review_feedback["at"],
            "failed_stage": submission.failed_stage if submission is not None else task_record.failed_stage,
            "error_message": submission.error_message if submission is not None else task_record.error_message,
        }
    )
    return payload


def _get_task_view_serializer(view: ProjectTaskView):
    if view == ProjectTaskView.MY:
        return _serialize_my_task
    if view == ProjectTaskView.SENSITIVE_REVIEW:
        return _serialize_sensitive_review_task
    return _serialize_overview_task


def _bonus_log_payloads(session, task_id: str) -> list[dict]:
    rows = session.execute(
        select(TaskBonusLogRecord).where(TaskBonusLogRecord.task_id == task_id).order_by(TaskBonusLogRecord.created_at)
    ).scalars().all()
    return [
        {
            "id": row.id,
            "submission_id": row.submission_id,
            "version_no": row.version_no,
            "bonus_points": row.bonus_points,
            "reason_code": row.reason_code,
            "reason_detail": row.reason_detail,
            "approved_by": row.approved_by,
            "approved_at": row.approved_at.isoformat(),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def _activity_log_payloads(session, task_id: str) -> list[dict]:
    rows = session.execute(
        select(TaskActivityLogRecord)
        .where(TaskActivityLogRecord.task_id == task_id)
        .order_by(TaskActivityLogRecord.created_at)
    ).scalars().all()
    return [
        {
            "id": row.id,
            "submission_id": row.submission_id,
            "actor_user_id": row.actor_user_id,
            "action_type": row.action_type,
            "from_work_status": row.from_work_status,
            "to_work_status": row.to_work_status,
            "from_score_lock_status": row.from_score_lock_status,
            "to_score_lock_status": row.to_score_lock_status,
            "metadata": row.metadata_json,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


def _latest_review_feedback_payload(session, task_id: str) -> dict:
    latest_review_log = session.execute(
        select(TaskActivityLogRecord)
        .where(
            TaskActivityLogRecord.task_id == task_id,
            TaskActivityLogRecord.action_type.in_(["REQUEST_CHANGES", "APPROVE"]),
        )
        .order_by(TaskActivityLogRecord.created_at.desc())
    ).scalars().first()

    if latest_review_log is None:
        return {
            "type": None,
            "reason": None,
            "at": None,
        }

    metadata = _parse_activity_metadata(latest_review_log.metadata_json)
    if latest_review_log.action_type == "REQUEST_CHANGES":
        return {
            "type": "changes_requested",
            "reason": metadata.get("reason"),
            "at": latest_review_log.created_at.isoformat(),
        }

    return {
        "type": "approved",
        "reason": metadata.get("comment"),
        "at": latest_review_log.created_at.isoformat(),
    }


def _parse_activity_metadata(metadata_json: str | None) -> dict:
    if not metadata_json:
        return {}
    try:
        parsed = json.loads(metadata_json)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _validate_parent_task_project(session, project_id: str, parent_task_id: str | None) -> None:
    if not parent_task_id:
        return

    parent = session.get(TaskRecord, parent_task_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parent task not found")
    if parent.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="parent task must belong to the same project",
        )


def _ensure_team_member(
    session,
    team_id: str,
    user_id: str,
    team_role: str | None,
    joined_at: datetime,
) -> TeamMemberRecord:
    stmt = select(TeamMemberRecord).where(
        TeamMemberRecord.team_id == team_id,
        TeamMemberRecord.user_id == user_id,
    )
    member = session.execute(stmt).scalars().first()
    if member is not None:
        if team_role:
            member.team_role = team_role
        return member

    member = TeamMemberRecord(
        id=str(uuid4()),
        team_id=team_id,
        user_id=user_id,
        team_role=team_role,
        joined_at=joined_at,
    )
    session.add(member)
    return member


def _ensure_project_member(
    *,
    session,
    project_id: str,
    user_id: str,
    display_name: str | None,
    role: str,
    joined_at: datetime,
) -> ProjectMemberRecord:
    stmt = select(ProjectMemberRecord).where(
        ProjectMemberRecord.project_id == project_id,
        ProjectMemberRecord.user_id == user_id,
    )
    member = session.execute(stmt).scalars().first()
    if member is not None:
        member.role = role
        member.display_name = display_name or member.display_name
        return member

    member = ProjectMemberRecord(
        id=str(uuid4()),
        project_id=project_id,
        user_id=user_id,
        display_name=display_name,
        role=role,
        joined_at=joined_at,
    )
    session.add(member)
    return member


def _count_project_owners(session, project_id: str) -> int:
    rows = session.execute(
        select(ProjectMemberRecord).where(
            ProjectMemberRecord.project_id == project_id,
            ProjectMemberRecord.role == ProjectRole.OWNER.value,
        )
    ).scalars().all()
    return len(rows)


def _count_project_leads(session, project_id: str) -> int:
    rows = session.execute(
        select(ProjectMemberRecord).where(
            ProjectMemberRecord.project_id == project_id,
            ProjectMemberRecord.role.in_([ProjectRole.OWNER.value, ProjectRole.MANAGER.value]),
        )
    ).scalars().all()
    return len(rows)


def _get_project_member(session, project_id: str, user_id: str) -> ProjectMemberRecord | None:
    return session.execute(
        select(ProjectMemberRecord).where(
            ProjectMemberRecord.project_id == project_id,
            ProjectMemberRecord.user_id == user_id,
        )
    ).scalars().first()


def _count_team_owners(session, team_id: str) -> int:
    rows = session.execute(
        select(TeamMemberRecord).where(
            TeamMemberRecord.team_id == team_id,
            TeamMemberRecord.team_role == ProjectRole.OWNER.value,
        )
    ).scalars().all()
    return len(rows)


def _get_team_or_404(session, team_id: str) -> TeamRecord:
    team = session.get(TeamRecord, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="team not found")
    return team


def _get_team_member(session, team_id: str, user_id: str) -> TeamMemberRecord | None:
    return session.execute(
        select(TeamMemberRecord).where(
            TeamMemberRecord.team_id == team_id,
            TeamMemberRecord.user_id == user_id,
        )
    ).scalars().first()


def _require_team_member(session, team_id: str, user_id: str) -> TeamMemberRecord:
    member = _get_team_member(session, team_id, user_id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="team membership required")
    return member


def _require_team_manage_access(session, team_id: str, user_id: str) -> TeamMemberRecord:
    member = _require_team_member(session, team_id, user_id)
    if member.team_role not in {ProjectRole.OWNER.value, ProjectRole.MANAGER.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner or manager role required")
    return member


def _require_team_owner_access(session, team_id: str, user_id: str) -> TeamMemberRecord:
    member = _require_team_member(session, team_id, user_id)
    if member.team_role != ProjectRole.OWNER.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="owner role required")
    return member


def _project_response(project: ProjectRecord, current_user_role: str | None = None) -> ProjectResponse:
    return ProjectResponse(
        project_id=project.id,
        team_id=project.team_id,
        name=project.name,
        description=project.description,
        created_by=project.created_by,
        current_user_role=current_user_role,
        created_at=project.created_at.isoformat(),
    )


def _project_member_response(member: ProjectMemberRecord, user: UserProfileRecord | None = None) -> ProjectMemberResponse:
    return ProjectMemberResponse(
        project_member_id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        email=user.email if user else None,
        display_name=member.display_name,
        role=ProjectRole(member.role),
        joined_at=member.joined_at.isoformat(),
    )


def _team_member_response(member: TeamMemberRecord, user: UserProfileRecord | None = None) -> TeamMemberResponse:
    return TeamMemberResponse(
        team_member_id=member.id,
        team_id=member.team_id,
        user_id=member.user_id,
        email=user.email if user else None,
        display_name=user.display_name if user else None,
        role=ProjectRole(member.team_role) if member.team_role else None,
        joined_at=member.joined_at.isoformat(),
    )


def _now() -> datetime:
    return datetime.now(UTC)
