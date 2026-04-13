from pydantic import BaseModel, Field

from app.models import ProjectRole


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    created_by: str | None = None


class TeamUpdateRequest(BaseModel):
    name: str = Field(min_length=1)


class TeamResponse(BaseModel):
    team_id: str
    name: str
    created_by: str | None = None
    current_user_role: str | None = None
    created_at: str


class TeamListResponse(BaseModel):
    teams: list[TeamResponse]


class TeamMemberAddRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3)
    user_id: str | None = Field(default=None, min_length=1)
    role: ProjectRole


class TeamMemberUpdateRequest(BaseModel):
    role: ProjectRole


class TeamMemberResponse(BaseModel):
    team_member_id: str
    team_id: str
    user_id: str
    email: str | None = None
    display_name: str | None = None
    role: ProjectRole | None = None
    joined_at: str


class TeamMemberListResponse(BaseModel):
    team_id: str
    members: list[TeamMemberResponse]


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    created_by: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    team_id: str | None = Field(default=None, min_length=1)


class ProjectResponse(BaseModel):
    project_id: str
    team_id: str
    name: str
    description: str | None = None
    created_by: str | None = None
    current_user_role: str | None = None
    created_at: str


class ProjectListResponse(BaseModel):
    team_id: str
    projects: list[ProjectResponse]


class ProjectMemberAddRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3)
    user_id: str | None = Field(default=None, min_length=1)
    display_name: str | None = None
    role: ProjectRole


class ProjectMemberUpdateRequest(BaseModel):
    role: ProjectRole
    display_name: str | None = None


class ProjectMemberResponse(BaseModel):
    project_member_id: str
    project_id: str
    user_id: str
    email: str | None = None
    display_name: str | None = None
    role: ProjectRole
    joined_at: str


class ProjectMemberListResponse(BaseModel):
    project_id: str
    members: list[ProjectMemberResponse]


class ProjectTaskReadItemResponse(BaseModel):
    task_id: str
    project_id: str
    parent_task_id: str | None = None
    user_id: str | None = None
    user_name: str | None = None
    title: str
    task_type: str
    task_goal: str
    task_weight: int
    status: str
    work_status: str
    evaluation_status: str | None = None
    score_lock_status: str
    has_submission: bool
    current_submission_id: str | None = None
    current_submission_version_no: int | None = None
    submission_content: str | None = None
    submitted_at: str | None = None
    approved_version_no: int | None = None
    ai_question: str | None = None
    user_answer: str | None = None
    raw_score: int | None = None
    weighted_score: int | None = None
    ai_factor: float | None = None
    provisional_score: float | None = None
    ai_comment: str | None = None
    final_score: float | None = None
    locked_main_score: float | None = None
    total_delta_bonus: float | None = None
    latest_review_feedback_type: str | None = None
    latest_review_feedback_reason: str | None = None
    latest_review_feedback_at: str | None = None
    failed_stage: str | None = None
    error_message: str | None = None
    bonus_logs: list[dict] | None = None
    activity_logs: list[dict] | None = None
    created_at: str
    updated_at: str


class ProjectTaskReadListResponse(BaseModel):
    project_id: str
    view: str
    tasks: list[ProjectTaskReadItemResponse]
