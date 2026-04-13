import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import (
    ScoreLockStatus,
    TaskActivityAction,
    TaskActivityLogRecord,
    TaskBonusLogRecord,
    TaskRecord,
    TaskStatus,
    TaskSubmissionRecord,
    TaskWorkStatus,
)
from app.schemas import (
    ContributionResponse,
    MemberContribution,
    ProjectTaskItemResponse,
    ProjectTaskListResponse,
    TaskAnswerRequest,
    TaskAnswerResponse,
    TaskApproveRequest,
    TaskApproveResponse,
    TaskCancelRequest,
    TaskCancelResponse,
    TaskCloseRequest,
    TaskCloseResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskDeleteResponse,
    TaskDeltaBonusRequest,
    TaskDeltaBonusResponse,
    TaskRequestChangesRequest,
    TaskRequestChangesResponse,
    TaskReopenRequest,
    TaskReopenResponse,
    TaskRetryResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskUpdateRequest,
    TaskUpdateResponse,
)
from app.services.ai_service import AIProviderException, generate_question, score_answer
from app.services.project_membership import get_project_member


DEFAULT_MEMBER_NAME = "임시 사용자"
DEFAULT_ACTOR_ID = "system"


def create_task(payload: TaskCreateRequest, actor_user_id: str | None = None) -> TaskCreateResponse:
    now = _now()
    task_id = str(uuid4())
    user_id = payload.user_id or actor_user_id or None
    user_name = payload.user_name or DEFAULT_MEMBER_NAME

    with get_db_session() as session:
        if payload.parent_task_id:
            parent_task = session.get(TaskRecord, payload.parent_task_id)
            if parent_task is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parent task not found")
            if parent_task.project_id != payload.project_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="parent task must belong to the same project",
                )

        task_record = TaskRecord(
            id=task_id,
            project_id=payload.project_id,
            parent_task_id=payload.parent_task_id,
            user_id=user_id,
            user_name=user_name,
            creator_user_id=actor_user_id or user_id,
            title=payload.title,
            task_type=payload.task_type,
            task_goal=payload.task_goal,
            task_weight=payload.task_weight,
            status=TaskStatus.TODO.value,
            work_status=TaskWorkStatus.IN_PROGRESS.value,
            score_lock_status=ScoreLockStatus.UNLOCKED.value,
            base_points=float(payload.task_weight),
            locked_main_score=None,
            total_delta_bonus=0,
            approved_version_no=None,
            approved_submission_id=None,
            approved_by=None,
            approved_at=None,
            closed_by=None,
            closed_at=None,
            canceled_by=None,
            canceled_at=None,
            content=None,
            ai_question=None,
            user_answer=None,
            raw_score=None,
            weighted_score=None,
            ai_comment=None,
            failed_stage=None,
            error_message=None,
            created_at=now,
            updated_at=now,
            submitted_at=None,
            scored_at=None,
        )
        session.add(task_record)
        session.flush()
        return TaskCreateResponse(**_base_task_payload(task_record))


def update_task(task_id: str, payload: TaskUpdateRequest, actor_user_id: str | None = None) -> TaskUpdateResponse:
    _ = actor_user_id
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        _require_todo_task(task_record, "edited")

        assignee = get_project_member(session, task_record.project_id, payload.user_id)
        if assignee is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assignee must be a project member",
            )

        task_record.user_id = payload.user_id
        task_record.user_name = payload.user_name or assignee.display_name or payload.user_id
        task_record.title = payload.title
        task_record.task_type = payload.task_type
        task_record.task_goal = payload.task_goal
        task_record.task_weight = payload.task_weight
        task_record.base_points = float(payload.task_weight)
        task_record.updated_at = _now()
        session.flush()

        return TaskUpdateResponse(
            task_id=task_record.id,
            project_id=task_record.project_id,
            parent_task_id=task_record.parent_task_id,
            user_id=task_record.user_id,
            user_name=task_record.user_name,
            title=task_record.title,
            task_type=task_record.task_type,
            task_goal=task_record.task_goal,
            task_weight=task_record.task_weight,
            status=TaskStatus(task_record.status),
            work_status=TaskWorkStatus(task_record.work_status),
            score_lock_status=ScoreLockStatus(task_record.score_lock_status),
            base_points=task_record.base_points,
            approved_version_no=task_record.approved_version_no,
            updated_at=task_record.updated_at.isoformat(),
        )


def delete_task(task_id: str, actor_user_id: str | None = None) -> TaskDeleteResponse:
    _ = actor_user_id
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        _require_todo_task(task_record, "deleted")

        if _get_latest_submission(session, task_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="only TODO task can be deleted",
            )

        deleted_at = _now()
        project_id = task_record.project_id
        session.delete(task_record)
        session.flush()

        return TaskDeleteResponse(
            task_id=task_id,
            project_id=project_id,
            deleted=True,
            deleted_at=deleted_at.isoformat(),
        )


def submit_task(task_id: str, payload: TaskSubmitRequest, actor_user_id: str | None = None) -> TaskSubmitResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        if task_record.status != TaskStatus.TODO.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="submit is only allowed when status is TODO",
            )

        next_version_no = _next_submission_version_no(session, task_id)
        now = _now()
        submission = TaskSubmissionRecord(
            id=str(uuid4()),
            task_id=task_id,
            version_no=next_version_no,
            submission_content=payload.content,
            submission_note=None,
            evaluation_status=TaskStatus.GENERATING_Q.value,
            ai_question=None,
            user_answer=None,
            raw_score=None,
            ai_factor=None,
            provisional_score=None,
            ai_comment=None,
            failed_stage=None,
            error_message=None,
            retry_count=0,
            submitted_by=actor_user_id or task_record.user_id,
            submitted_at=now,
            question_generated_at=None,
            answered_at=None,
            scored_at=None,
            last_retried_at=None,
            created_at=now,
            updated_at=now,
        )
        session.add(submission)

        task_record.content = payload.content
        task_record.status = TaskStatus.GENERATING_Q.value
        task_record.work_status = TaskWorkStatus.SUBMITTED_FOR_REVIEW.value
        task_record.submitted_at = now
        task_record.updated_at = now
        task_record.failed_stage = None
        task_record.error_message = None
        session.flush()

        try:
            submission.ai_question = generate_question(
                title=task_record.title,
                task_type=task_record.task_type,
                task_goal=task_record.task_goal,
                content=submission.submission_content or "",
            )
            submission.evaluation_status = TaskStatus.AWAITING_A.value
            submission.question_generated_at = _now()
            submission.updated_at = submission.question_generated_at
            task_record.ai_question = submission.ai_question
            task_record.status = TaskStatus.AWAITING_A.value
            task_record.updated_at = submission.question_generated_at
            session.flush()
        except AIProviderException as exc:
            _mark_submission_failed(session, task_record, submission, TaskStatus.GENERATING_Q.value, str(exc))
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ai question generation failed",
            ) from exc

        return TaskSubmitResponse(
            task_id=task_record.id,
            submission_id=submission.id,
            version_no=submission.version_no,
            status=TaskStatus(task_record.status),
            work_status=TaskWorkStatus(task_record.work_status),
            content=task_record.content or "",
            ai_question=task_record.ai_question,
        )


def answer_task(task_id: str, payload: TaskAnswerRequest) -> TaskAnswerResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        submission = _get_latest_submission(session, task_id)

        if submission is None or submission.evaluation_status != TaskStatus.AWAITING_A.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="answer is only allowed when status is AWAITING_A",
            )

        now = _now()
        submission.user_answer = payload.user_answer
        submission.answered_at = now
        submission.evaluation_status = TaskStatus.SCORING.value
        submission.updated_at = now
        submission.failed_stage = None
        submission.error_message = None

        task_record.user_answer = payload.user_answer
        task_record.status = TaskStatus.SCORING.value
        task_record.updated_at = now
        task_record.failed_stage = None
        task_record.error_message = None
        session.flush()

        try:
            score_result = score_answer(
                title=task_record.title,
                task_type=task_record.task_type,
                task_goal=task_record.task_goal,
                content=submission.submission_content or "",
                ai_question=submission.ai_question or "",
                user_answer=submission.user_answer or "",
            )
        except AIProviderException as exc:
            _mark_submission_failed(session, task_record, submission, TaskStatus.SCORING.value, str(exc))
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ai scoring failed",
            ) from exc

        ai_factor = _map_ai_factor(score_result.raw_score)
        provisional_score = round(task_record.base_points * ai_factor, 2)
        weighted_score = score_result.raw_score * task_record.task_weight
        scored_at = _now()

        submission.raw_score = score_result.raw_score
        submission.ai_factor = ai_factor
        submission.provisional_score = provisional_score
        submission.ai_comment = score_result.comment
        submission.evaluation_status = TaskStatus.DONE.value
        submission.scored_at = scored_at
        submission.updated_at = scored_at

        task_record.raw_score = score_result.raw_score
        task_record.weighted_score = weighted_score
        task_record.ai_comment = score_result.comment
        task_record.status = TaskStatus.DONE.value
        task_record.scored_at = scored_at
        task_record.updated_at = scored_at
        session.flush()

        return TaskAnswerResponse(
            task_id=task_record.id,
            submission_id=submission.id,
            version_no=submission.version_no,
            status=TaskStatus(task_record.status),
            user_answer=submission.user_answer or "",
            raw_score=submission.raw_score,
            weighted_score=task_record.weighted_score,
            ai_comment=submission.ai_comment,
            provisional_score=submission.provisional_score,
        )


def retry_task(task_id: str, actor_user_id: str | None = None) -> TaskRetryResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        submission = _get_latest_submission(session, task_id)

        if submission is None or submission.evaluation_status != TaskStatus.FAILED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="retry is only allowed when status is FAILED",
            )

        failed_stage = submission.failed_stage
        now = _now()

        if failed_stage == TaskStatus.GENERATING_Q.value:
            submission.evaluation_status = TaskStatus.TODO.value
            submission.ai_question = None
            task_record.status = TaskStatus.TODO.value
            task_record.ai_question = None
        elif failed_stage == TaskStatus.SCORING.value:
            submission.evaluation_status = TaskStatus.AWAITING_A.value
            submission.raw_score = None
            submission.ai_factor = None
            submission.provisional_score = None
            submission.ai_comment = None
            submission.scored_at = None
            task_record.status = TaskStatus.AWAITING_A.value
            task_record.raw_score = None
            task_record.weighted_score = None
            task_record.ai_comment = None
            task_record.scored_at = None
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="retry requires a supported failed_stage",
            )

        submission.retry_count += 1
        submission.last_retried_at = now
        submission.error_message = None
        submission.failed_stage = None
        submission.updated_at = now

        task_record.error_message = None
        task_record.failed_stage = None
        task_record.updated_at = now
        session.flush()

        return TaskRetryResponse(**_base_task_payload(task_record))


def approve_task(task_id: str, payload: TaskApproveRequest, actor_user_id: str | None = None) -> TaskApproveResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        submission = _get_latest_submission(session, task_id)

        if submission is None or submission.evaluation_status != TaskStatus.DONE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="approve requires a DONE submission",
            )

        actor = actor_user_id or payload.approved_by or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_work_status = task_record.work_status
        from_score_lock_status = task_record.score_lock_status

        task_record.work_status = TaskWorkStatus.APPROVED.value
        task_record.score_lock_status = ScoreLockStatus.LOCKED.value
        task_record.approved_version_no = submission.version_no
        task_record.approved_submission_id = submission.id
        task_record.approved_by = actor
        task_record.approved_at = now
        task_record.locked_main_score = submission.provisional_score or float(task_record.weighted_score or 0)
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            submission.id,
            actor,
            TaskActivityAction.APPROVE.value,
            from_work_status,
            task_record.work_status,
            from_score_lock_status,
            task_record.score_lock_status,
            {"comment": payload.comment},
        )

        return TaskApproveResponse(
            task_id=task_record.id,
            work_status=TaskWorkStatus(task_record.work_status),
            score_lock_status=ScoreLockStatus(task_record.score_lock_status),
            approved_version_no=task_record.approved_version_no or 0,
            locked_main_score=task_record.locked_main_score or 0,
            total_delta_bonus=task_record.total_delta_bonus,
        )


def request_changes_task(task_id: str, payload: TaskRequestChangesRequest, actor_user_id: str | None = None) -> TaskRequestChangesResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        submission = _get_latest_submission(session, task_id)

        if submission is None or submission.evaluation_status != TaskStatus.DONE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="request changes requires a DONE submission",
            )
        if (
            task_record.work_status == TaskWorkStatus.APPROVED.value
            or task_record.score_lock_status in {ScoreLockStatus.LOCKED.value, ScoreLockStatus.LOCKED_WITH_BONUS.value}
            or task_record.approved_version_no is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="request changes is not allowed after approval",
            )

        actor = actor_user_id or payload.actor_user_id or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_work_status = task_record.work_status

        task_record.work_status = TaskWorkStatus.CHANGES_REQUESTED.value
        task_record.status = TaskStatus.TODO.value
        task_record.ai_question = None
        task_record.raw_score = None
        task_record.weighted_score = None
        task_record.ai_comment = None
        task_record.failed_stage = None
        task_record.error_message = None
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            submission.id,
            actor,
            TaskActivityAction.REQUEST_CHANGES.value,
            from_work_status,
            task_record.work_status,
            task_record.score_lock_status,
            task_record.score_lock_status,
            {"reason": payload.reason},
        )

        return TaskRequestChangesResponse(
            task_id=task_record.id,
            work_status=TaskWorkStatus(task_record.work_status),
            score_lock_status=ScoreLockStatus(task_record.score_lock_status),
            message="same task can submit a new version",
        )


def close_task(task_id: str, payload: TaskCloseRequest, actor_user_id: str | None = None) -> TaskCloseResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        if task_record.work_status != TaskWorkStatus.APPROVED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="close requires APPROVED work_status",
            )

        actor = actor_user_id or payload.actor_user_id or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_work_status = task_record.work_status

        task_record.work_status = TaskWorkStatus.CLOSED.value
        task_record.closed_by = actor
        task_record.closed_at = now
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            task_record.approved_submission_id,
            actor,
            TaskActivityAction.CLOSE.value,
            from_work_status,
            task_record.work_status,
            task_record.score_lock_status,
            task_record.score_lock_status,
            {"reason": payload.reason},
        )

        return TaskCloseResponse(
            task_id=task_record.id,
            work_status=TaskWorkStatus(task_record.work_status),
            closed_at=now.isoformat(),
        )


def cancel_task(task_id: str, payload: TaskCancelRequest, actor_user_id: str | None = None) -> TaskCancelResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        actor = actor_user_id or payload.actor_user_id or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_work_status = task_record.work_status

        task_record.work_status = TaskWorkStatus.CANCELED.value
        task_record.canceled_by = actor
        task_record.canceled_at = now
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            _get_latest_submission_id(session, task_id),
            actor,
            TaskActivityAction.CANCEL.value,
            from_work_status,
            task_record.work_status,
            task_record.score_lock_status,
            task_record.score_lock_status,
            {"reason": payload.reason},
        )

        return TaskCancelResponse(
            task_id=task_record.id,
            work_status=TaskWorkStatus(task_record.work_status),
            canceled_at=now.isoformat(),
        )


def reopen_task(task_id: str, payload: TaskReopenRequest, actor_user_id: str | None = None) -> TaskReopenResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        actor = actor_user_id or payload.actor_user_id or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_work_status = task_record.work_status
        from_score_lock_status = task_record.score_lock_status

        task_record.work_status = TaskWorkStatus.IN_PROGRESS.value
        task_record.score_lock_status = ScoreLockStatus.UNLOCKED.value
        task_record.approved_version_no = None
        task_record.approved_submission_id = None
        task_record.approved_by = None
        task_record.approved_at = None
        task_record.locked_main_score = None
        task_record.total_delta_bonus = 0
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            _get_latest_submission_id(session, task_id),
            actor,
            TaskActivityAction.REOPEN.value,
            from_work_status,
            task_record.work_status,
            from_score_lock_status,
            task_record.score_lock_status,
            {"reason": payload.reason},
        )

        return TaskReopenResponse(
            task_id=task_record.id,
            work_status=TaskWorkStatus(task_record.work_status),
            score_lock_status=ScoreLockStatus(task_record.score_lock_status),
            message="task reopened and score lock cleared",
        )


def grant_delta_bonus(task_id: str, payload: TaskDeltaBonusRequest, actor_user_id: str | None = None) -> TaskDeltaBonusResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)
        submission = _get_latest_submission(session, task_id)

        if task_record.score_lock_status not in {
            ScoreLockStatus.LOCKED.value,
            ScoreLockStatus.LOCKED_WITH_BONUS.value,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="delta bonus requires locked score status",
            )

        actor = actor_user_id or payload.actor_user_id or task_record.user_id or DEFAULT_ACTOR_ID
        now = _now()
        from_score_lock_status = task_record.score_lock_status

        bonus_log = TaskBonusLogRecord(
            id=str(uuid4()),
            task_id=task_id,
            submission_id=submission.id if submission is not None else None,
            version_no=submission.version_no if submission is not None else None,
            bonus_points=payload.bonus_points,
            reason_code=payload.reason_code,
            reason_detail=payload.reason_detail,
            approved_by=actor,
            approved_at=now,
            created_at=now,
        )
        session.add(bonus_log)

        task_record.total_delta_bonus = round((task_record.total_delta_bonus or 0) + payload.bonus_points, 2)
        task_record.score_lock_status = ScoreLockStatus.LOCKED_WITH_BONUS.value
        task_record.updated_at = now
        session.flush()

        _create_activity_log(
            session,
            task_record,
            bonus_log.submission_id,
            actor,
            TaskActivityAction.DELTA_BONUS_GRANTED.value,
            task_record.work_status,
            task_record.work_status,
            from_score_lock_status,
            task_record.score_lock_status,
            {
                "bonus_points": payload.bonus_points,
                "reason_code": payload.reason_code,
                "reason_detail": payload.reason_detail,
            },
        )

        return TaskDeltaBonusResponse(
            task_id=task_record.id,
            score_lock_status=ScoreLockStatus(task_record.score_lock_status),
            locked_main_score=task_record.locked_main_score,
            total_delta_bonus=task_record.total_delta_bonus,
        )


def get_project_contribution(project_id: str) -> ContributionResponse:
    with get_db_session() as session:
        stmt = select(TaskRecord).where(TaskRecord.project_id == project_id)
        task_records = session.execute(stmt).scalars().all()

        grouped: dict[str, dict[str, int | float | str]] = {}
        for task_record in task_records:
            name = task_record.user_name or DEFAULT_MEMBER_NAME
            if name not in grouped:
                grouped[name] = {"name": name, "completed_tasks": 0, "total_weighted_score": 0.0}

            if task_record.locked_main_score is not None:
                grouped[name]["completed_tasks"] += 1
                grouped[name]["total_weighted_score"] += (
                    (task_record.locked_main_score or 0) + (task_record.total_delta_bonus or 0)
                )
            elif task_record.status == TaskStatus.DONE.value and task_record.weighted_score is not None:
                grouped[name]["completed_tasks"] += 1
                grouped[name]["total_weighted_score"] += task_record.weighted_score

        contributions = [
            MemberContribution(
                name=item["name"],
                completed_tasks=int(item["completed_tasks"]),
                total_weighted_score=item["total_weighted_score"],
            )
            for item in sorted(
                grouped.values(),
                key=lambda item: (-float(item["total_weighted_score"]), str(item["name"])),
            )
        ]

        return ContributionResponse(project_id=project_id, contributions=contributions)


def list_project_tasks(project_id: str) -> ProjectTaskListResponse:
    with get_db_session() as session:
        stmt = select(TaskRecord).where(TaskRecord.project_id == project_id).order_by(
            TaskRecord.created_at.desc(),
            TaskRecord.id.desc(),
        )
        task_records = session.execute(stmt).scalars().all()

        tasks = []
        for task_record in task_records:
            submission = _get_latest_submission(session, task_record.id)
            tasks.append(
                ProjectTaskItemResponse(
                    task_id=task_record.id,
                    project_id=task_record.project_id,
                    parent_task_id=task_record.parent_task_id,
                    user_id=task_record.user_id,
                    user_name=task_record.user_name or DEFAULT_MEMBER_NAME,
                    title=task_record.title,
                    task_type=task_record.task_type,
                    task_goal=task_record.task_goal,
                    task_weight=task_record.task_weight,
                    content=task_record.content,
                    ai_question=task_record.ai_question,
                    user_answer=task_record.user_answer,
                    raw_score=task_record.raw_score,
                    weighted_score=task_record.weighted_score,
                    ai_comment=task_record.ai_comment,
                    status=TaskStatus(task_record.status),
                    work_status=TaskWorkStatus(task_record.work_status),
                    score_lock_status=ScoreLockStatus(task_record.score_lock_status),
                    base_points=task_record.base_points,
                    locked_main_score=task_record.locked_main_score,
                    total_delta_bonus=task_record.total_delta_bonus,
                    approved_version_no=task_record.approved_version_no,
                    current_submission_id=submission.id if submission is not None else None,
                    current_submission_version_no=submission.version_no if submission is not None else None,
                    failed_stage=task_record.failed_stage,
                    error_message=task_record.error_message,
                    created_at=task_record.created_at.isoformat(),
                    updated_at=task_record.updated_at.isoformat(),
                )
            )

        return ProjectTaskListResponse(project_id=project_id, tasks=tasks)


def _get_task(session: Session, task_id: str) -> TaskRecord:
    task_record = session.get(TaskRecord, task_id)
    if task_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return task_record


def _require_todo_task(task_record: TaskRecord, action: str) -> None:
    if task_record.status != TaskStatus.TODO.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"only TODO task can be {action}",
        )


def _get_latest_submission(session: Session, task_id: str) -> TaskSubmissionRecord | None:
    stmt = (
        select(TaskSubmissionRecord)
        .where(TaskSubmissionRecord.task_id == task_id)
        .order_by(TaskSubmissionRecord.version_no.desc())
    )
    return session.execute(stmt).scalars().first()


def _get_latest_submission_id(session: Session, task_id: str) -> str | None:
    submission = _get_latest_submission(session, task_id)
    return submission.id if submission is not None else None


def _next_submission_version_no(session: Session, task_id: str) -> int:
    stmt = select(func.max(TaskSubmissionRecord.version_no)).where(TaskSubmissionRecord.task_id == task_id)
    current = session.execute(stmt).scalar_one()
    return 1 if current is None else int(current) + 1


def _mark_submission_failed(
    session: Session,
    task_record: TaskRecord,
    submission: TaskSubmissionRecord,
    failed_stage: str,
    error_message: str,
) -> None:
    now = _now()
    submission.evaluation_status = TaskStatus.FAILED.value
    submission.failed_stage = failed_stage
    submission.error_message = error_message
    submission.updated_at = now

    task_record.status = TaskStatus.FAILED.value
    task_record.failed_stage = failed_stage
    task_record.error_message = error_message
    task_record.updated_at = now
    session.flush()


def _create_activity_log(
    session: Session,
    task_record: TaskRecord,
    submission_id: str | None,
    actor_user_id: str | None,
    action_type: str,
    from_work_status: str | None,
    to_work_status: str | None,
    from_score_lock_status: str | None,
    to_score_lock_status: str | None,
    metadata: dict | None,
) -> None:
    log_record = TaskActivityLogRecord(
        id=str(uuid4()),
        task_id=task_record.id,
        submission_id=submission_id,
        actor_user_id=actor_user_id,
        action_type=action_type,
        from_work_status=from_work_status,
        to_work_status=to_work_status,
        from_score_lock_status=from_score_lock_status,
        to_score_lock_status=to_score_lock_status,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        created_at=_now(),
    )
    session.add(log_record)
    session.flush()


def _map_ai_factor(raw_score: int) -> float:
    return {
        1: 0.70,
        2: 0.85,
        3: 1.00,
        4: 1.10,
        5: 1.20,
    }[raw_score]


def _base_task_payload(task_record: TaskRecord) -> dict:
    return {
        "task_id": task_record.id,
        "project_id": task_record.project_id,
        "parent_task_id": task_record.parent_task_id,
        "title": task_record.title,
        "task_type": task_record.task_type,
        "task_goal": task_record.task_goal,
        "task_weight": task_record.task_weight,
        "status": TaskStatus(task_record.status),
        "work_status": TaskWorkStatus(task_record.work_status),
        "score_lock_status": ScoreLockStatus(task_record.score_lock_status),
        "base_points": task_record.base_points,
        "approved_version_no": task_record.approved_version_no,
    }


def _now() -> datetime:
    return datetime.now(UTC)
