from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import TaskRecord, TaskStatus
from app.schemas import (
    ContributionResponse,
    MemberContribution,
    ProjectTaskItemResponse,
    ProjectTaskListResponse,
    TaskAnswerRequest,
    TaskAnswerResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskRetryResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
)
from app.services.ai_service import AIProviderException, generate_question, score_answer


DEFAULT_MEMBER_NAME = "임시 사용자"


def create_task(payload: TaskCreateRequest) -> TaskCreateResponse:
    now = _now()
    task_id = str(uuid4())
    user_id = payload.user_id or None
    user_name = payload.user_name or DEFAULT_MEMBER_NAME

    with get_db_session() as session:
        task_record = TaskRecord(
            id=task_id,
            project_id=payload.project_id,
            user_id=user_id,
            user_name=user_name,
            title=payload.title,
            task_type=payload.task_type,
            task_goal=payload.task_goal,
            task_weight=payload.task_weight,
            # MVP 상태 흐름 시작점 반영
            status=TaskStatus.TODO.value,
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


def submit_task(task_id: str, payload: TaskSubmitRequest) -> TaskSubmitResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        # TODO 에서만 submit 가능 정책 반영
        if task_record.status != TaskStatus.TODO.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="submit is only allowed when status is TODO",
            )

        submitted_at = _now()
        task_record.content = payload.content
        task_record.status = TaskStatus.GENERATING_Q.value
        task_record.submitted_at = submitted_at
        task_record.updated_at = submitted_at
        task_record.failed_stage = None
        task_record.error_message = None
        session.flush()

        task_record.ai_question = generate_question(
            title=task_record.title,
            task_type=task_record.task_type,
            task_goal=task_record.task_goal,
            content=task_record.content or "",
        )
        task_record.status = TaskStatus.AWAITING_A.value
        task_record.updated_at = _now()
        session.flush()

        return TaskSubmitResponse(
            task_id=task_record.id,
            status=TaskStatus(task_record.status),
            content=task_record.content or "",
            ai_question=task_record.ai_question,
        )


def answer_task(task_id: str, payload: TaskAnswerRequest) -> TaskAnswerResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        # AWAITING_A 에서만 answer 가능 정책 반영
        if task_record.status != TaskStatus.AWAITING_A.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="answer is only allowed when status is AWAITING_A",
            )

        task_record.user_answer = payload.user_answer
        task_record.status = TaskStatus.SCORING.value
        task_record.updated_at = _now()
        task_record.failed_stage = None
        task_record.error_message = None
        session.flush()

        try:
            score_result = score_answer(
                title=task_record.title,
                task_type=task_record.task_type,
                task_goal=task_record.task_goal,
                content=task_record.content or "",
                ai_question=task_record.ai_question or "",
                user_answer=task_record.user_answer or "",
            )
        except AIProviderException as exc:
            task_record.status = TaskStatus.FAILED.value
            task_record.failed_stage = TaskStatus.SCORING.value
            task_record.error_message = str(exc)
            task_record.updated_at = _now()
            session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ai scoring failed",
            ) from exc

        task_record.raw_score = score_result.raw_score
        # raw_score * task_weight 정책 반영
        task_record.weighted_score = task_record.raw_score * task_record.task_weight
        task_record.ai_comment = score_result.comment
        task_record.status = TaskStatus.DONE.value
        task_record.scored_at = _now()
        task_record.updated_at = task_record.scored_at
        session.flush()

        return TaskAnswerResponse(
            task_id=task_record.id,
            status=TaskStatus(task_record.status),
            user_answer=task_record.user_answer or "",
            raw_score=task_record.raw_score,
            weighted_score=task_record.weighted_score,
            ai_comment=task_record.ai_comment,
        )


def retry_task(task_id: str) -> TaskRetryResponse:
    with get_db_session() as session:
        task_record = _get_task(session, task_id)

        if task_record.status != TaskStatus.FAILED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="retry is only allowed when status is FAILED",
            )

        # failed_stage 기반 복구 정책 반영
        failed_stage = task_record.failed_stage

        if failed_stage == TaskStatus.GENERATING_Q.value:
            task_record.status = TaskStatus.TODO.value
            task_record.ai_question = None
        elif failed_stage == TaskStatus.SCORING.value:
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

        task_record.error_message = None
        task_record.failed_stage = None
        task_record.updated_at = _now()
        session.flush()

        # TODO: Extend recovery branches if additional failed stages are introduced.
        return TaskRetryResponse(**_base_task_payload(task_record))


def get_project_contribution(project_id: str) -> ContributionResponse:
    with get_db_session() as session:
        stmt = select(
            func.coalesce(TaskRecord.user_name, DEFAULT_MEMBER_NAME).label("name"),
            func.count(TaskRecord.id).label("completed_tasks"),
            func.coalesce(func.sum(TaskRecord.weighted_score), 0).label("total_weighted_score"),
        ).where(
            TaskRecord.project_id == project_id,
            TaskRecord.status == TaskStatus.DONE.value,
        ).group_by(
            func.coalesce(TaskRecord.user_name, DEFAULT_MEMBER_NAME),
        ).order_by(
            func.coalesce(func.sum(TaskRecord.weighted_score), 0).desc(),
            func.coalesce(TaskRecord.user_name, DEFAULT_MEMBER_NAME).asc(),
        )
        rows = session.execute(stmt).all()

        contributions = [
            MemberContribution(
                name=name,
                completed_tasks=completed_tasks,
                total_weighted_score=total_weighted_score,
            )
            for name, completed_tasks, total_weighted_score in rows
        ]

        return ContributionResponse(project_id=project_id, contributions=contributions)


def list_project_tasks(project_id: str) -> ProjectTaskListResponse:
    with get_db_session() as session:
        stmt = select(TaskRecord).where(
            TaskRecord.project_id == project_id,
        ).order_by(
            TaskRecord.created_at.desc(),
            TaskRecord.id.desc(),
        )
        task_records = session.execute(stmt).scalars().all()

        tasks = [
            ProjectTaskItemResponse(
                task_id=task_record.id,
                project_id=task_record.project_id,
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
                failed_stage=task_record.failed_stage,
                error_message=task_record.error_message,
                created_at=task_record.created_at.isoformat(),
                updated_at=task_record.updated_at.isoformat(),
            )
            for task_record in task_records
        ]

        return ProjectTaskListResponse(project_id=project_id, tasks=tasks)


def _get_task(session: Session, task_id: str) -> TaskRecord:
    task_record = session.get(TaskRecord, task_id)
    if task_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="task not found",
        )
    return task_record


def _base_task_payload(task_record: TaskRecord) -> dict:
    return {
        "task_id": task_record.id,
        "project_id": task_record.project_id,
        "title": task_record.title,
        "task_type": task_record.task_type,
        "task_goal": task_record.task_goal,
        "task_weight": task_record.task_weight,
        "status": TaskStatus(task_record.status),
    }


def _now() -> datetime:
    return datetime.now(UTC)
