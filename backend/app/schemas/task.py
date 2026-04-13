from pydantic import BaseModel, Field

from app.models import ScoreLockStatus, TaskStatus, TaskWorkStatus


class TaskCreateRequest(BaseModel):
    project_id: str
    parent_task_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int = Field(ge=1, le=3)


class TaskCreateResponse(BaseModel):
    task_id: str
    project_id: str
    parent_task_id: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int
    status: TaskStatus
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    base_points: float
    approved_version_no: int | None = None


class TaskUpdateRequest(BaseModel):
    title: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    task_goal: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    user_name: str | None = None
    task_weight: int = Field(ge=1, le=3)


class TaskUpdateResponse(BaseModel):
    task_id: str
    project_id: str
    parent_task_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int
    status: TaskStatus
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    base_points: float
    approved_version_no: int | None = None
    updated_at: str


class TaskDeleteResponse(BaseModel):
    task_id: str
    project_id: str
    deleted: bool
    deleted_at: str


class TaskSubmitRequest(BaseModel):
    content: str


class TaskSubmitResponse(BaseModel):
    task_id: str
    submission_id: str
    version_no: int
    status: TaskStatus
    work_status: TaskWorkStatus
    content: str
    ai_question: str | None = None


class TaskAnswerRequest(BaseModel):
    user_answer: str


class TaskAnswerResponse(BaseModel):
    task_id: str
    submission_id: str
    version_no: int
    status: TaskStatus
    user_answer: str
    raw_score: int | None = None
    weighted_score: int | None = None
    ai_comment: str | None = None
    provisional_score: float | None = None


class TaskRetryResponse(BaseModel):
    task_id: str
    project_id: str
    parent_task_id: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int
    status: TaskStatus
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    approved_version_no: int | None = None


class TaskApproveRequest(BaseModel):
    approved_by: str | None = None
    comment: str | None = None


class TaskApproveResponse(BaseModel):
    task_id: str
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    approved_version_no: int
    locked_main_score: float
    total_delta_bonus: float


class TaskRequestChangesRequest(BaseModel):
    actor_user_id: str | None = None
    reason: str


class TaskRequestChangesResponse(BaseModel):
    task_id: str
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    message: str


class TaskCloseRequest(BaseModel):
    actor_user_id: str | None = None
    reason: str | None = None


class TaskCloseResponse(BaseModel):
    task_id: str
    work_status: TaskWorkStatus
    closed_at: str


class TaskCancelRequest(BaseModel):
    actor_user_id: str | None = None
    reason: str


class TaskCancelResponse(BaseModel):
    task_id: str
    work_status: TaskWorkStatus
    canceled_at: str


class TaskReopenRequest(BaseModel):
    actor_user_id: str | None = None
    reason: str


class TaskReopenResponse(BaseModel):
    task_id: str
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    message: str


class TaskDeltaBonusRequest(BaseModel):
    actor_user_id: str | None = None
    bonus_points: float = Field(gt=0)
    reason_code: str
    reason_detail: str | None = None


class TaskDeltaBonusResponse(BaseModel):
    task_id: str
    score_lock_status: ScoreLockStatus
    locked_main_score: float | None = None
    total_delta_bonus: float


class ProjectTaskItemResponse(BaseModel):
    task_id: str
    project_id: str
    parent_task_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int
    content: str | None = None
    ai_question: str | None = None
    user_answer: str | None = None
    raw_score: int | None = None
    weighted_score: int | None = None
    ai_comment: str | None = None
    status: TaskStatus
    work_status: TaskWorkStatus
    score_lock_status: ScoreLockStatus
    base_points: float
    locked_main_score: float | None = None
    total_delta_bonus: float
    approved_version_no: int | None = None
    current_submission_id: str | None = None
    current_submission_version_no: int | None = None
    failed_stage: str | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class ProjectTaskListResponse(BaseModel):
    project_id: str
    tasks: list[ProjectTaskItemResponse]
