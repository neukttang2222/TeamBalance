from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Query

from app.models import ProjectTaskView
from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models import TaskRecord
from app.schemas import (
    ContributionResponse,
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberAddRequest,
    ProjectMemberListResponse,
    ProjectMemberResponse,
    ProjectMemberUpdateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    ProjectTaskListResponse,
    ProjectTaskReadListResponse,
    TaskApproveRequest,
    TaskApproveResponse,
    TaskAnswerRequest,
    TaskAnswerResponse,
    TaskCancelRequest,
    TaskCancelResponse,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskDeleteResponse,
    TaskCloseRequest,
    TaskCloseResponse,
    TaskDeltaBonusRequest,
    TaskDeltaBonusResponse,
    TaskReopenRequest,
    TaskReopenResponse,
    TaskRequestChangesRequest,
    TaskRequestChangesResponse,
    TaskRetryResponse,
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskUpdateRequest,
    TaskUpdateResponse,
    TeamCreateRequest,
    TeamListResponse,
    TeamMemberAddRequest,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamMemberUpdateRequest,
    TeamResponse,
    TeamUpdateRequest,
    UserSearchResponse,
)
from app.services.auth_service import CurrentUser
from app.services.project_membership import (
    require_project_member,
    require_sensitive_review_access,
    require_task_create_access,
)
from app.services import (
    add_team_member,
    add_project_member,
    answer_task,
    approve_task,
    cancel_task,
    close_task,
    create_project,
    create_project_task,
    create_task,
    create_team,
    delete_task,
    delete_project,
    delete_team,
    grant_delta_bonus,
    get_project_contribution,
    list_team_members,
    list_team_projects,
    list_project_members,
    list_project_tasks,
    list_project_tasks_by_view,
    list_teams,
    remove_project_member,
    remove_team_member,
    reopen_task,
    request_changes_task,
    retry_task,
    submit_task,
    update_task,
    update_project,
    update_project_member,
    update_team,
    update_team_member,
)
from app.services.auth_service import search_users
from app.services.project_membership import get_project_member


router = APIRouter(tags=["tasks"])


@router.get("/users/search", response_model=UserSearchResponse)
def search_users_endpoint(
    q: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> UserSearchResponse:
    _ = current_user
    return search_users(q)


@router.post("/teams", response_model=TeamResponse, status_code=201)
def create_team_endpoint(
    payload: TeamCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamResponse:
    return create_team(payload, actor_user_id=current_user.id)


@router.get("/teams", response_model=TeamListResponse)
def list_teams_endpoint(current_user: CurrentUser = Depends(get_current_user)) -> TeamListResponse:
    return list_teams(current_user.id)


@router.patch("/teams/{team_id}", response_model=TeamResponse)
def update_team_endpoint(
    team_id: str,
    payload: TeamUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamResponse:
    return update_team(team_id, payload, current_user.id)


@router.delete("/teams/{team_id}", response_model=TeamResponse)
def delete_team_endpoint(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamResponse:
    return delete_team(team_id, current_user.id)


@router.get("/teams/{team_id}/members", response_model=TeamMemberListResponse)
def list_team_members_endpoint(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamMemberListResponse:
    return list_team_members(team_id, current_user.id)


@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
def add_team_member_endpoint(
    team_id: str,
    payload: TeamMemberAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamMemberResponse:
    return add_team_member(team_id, payload, current_user.id)


@router.patch("/teams/{team_id}/members/{target_user_id}", response_model=TeamMemberResponse)
def update_team_member_endpoint(
    team_id: str,
    target_user_id: str,
    payload: TeamMemberUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamMemberResponse:
    return update_team_member(team_id, target_user_id, payload, current_user.id)


@router.delete("/teams/{team_id}/members/{target_user_id}", response_model=TeamMemberResponse)
def remove_team_member_endpoint(
    team_id: str,
    target_user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> TeamMemberResponse:
    return remove_team_member(team_id, target_user_id, current_user.id)


@router.post("/teams/{team_id}/projects", response_model=ProjectResponse, status_code=201)
def create_project_endpoint(
    team_id: str,
    payload: ProjectCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectResponse:
    return create_project(team_id, payload, actor_user_id=current_user.id)


@router.get("/teams/{team_id}/projects", response_model=ProjectListResponse)
def list_team_projects_endpoint(
    team_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectListResponse:
    return list_team_projects(team_id, current_user.id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project_endpoint(
    project_id: str,
    payload: ProjectUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectResponse:
    return update_project(project_id, payload, current_user.id)


@router.delete("/projects/{project_id}", response_model=ProjectResponse)
def delete_project_endpoint(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectResponse:
    return delete_project(project_id, current_user.id)


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=201)
def add_project_member_endpoint(
    project_id: str,
    payload: ProjectMemberAddRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectMemberResponse:
    with get_db_session() as session:
        require_sensitive_review_access(session, project_id, current_user.id)
    return add_project_member(project_id, payload)


@router.get("/projects/{project_id}/members", response_model=ProjectMemberListResponse)
def list_project_members_endpoint(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectMemberListResponse:
    return list_project_members(project_id, current_user.id)


@router.patch("/projects/{project_id}/members/{target_user_id}", response_model=ProjectMemberResponse)
def update_project_member_endpoint(
    project_id: str,
    target_user_id: str,
    payload: ProjectMemberUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectMemberResponse:
    return update_project_member(project_id, target_user_id, payload, current_user.id)


@router.delete("/projects/{project_id}/members/{target_user_id}", response_model=ProjectMemberResponse)
def remove_project_member_endpoint(
    project_id: str,
    target_user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectMemberResponse:
    return remove_project_member(project_id, target_user_id, current_user.id)


@router.post("/tasks", response_model=TaskCreateResponse, status_code=201)
def create_task_endpoint(
    payload: TaskCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskCreateResponse:
    normalized_payload = payload.model_copy(
        update={
            "user_id": current_user.id,
            "user_name": current_user.display_name or current_user.email,
        }
    )
    return create_task(normalized_payload, actor_user_id=current_user.id)


@router.post("/projects/{project_id}/tasks", response_model=TaskCreateResponse, status_code=201)
def create_project_task_endpoint(
    project_id: str,
    payload: TaskCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskCreateResponse:
    return create_project_task(project_id, payload, current_user.id)


@router.post("/tasks/{task_id}/submit", response_model=TaskSubmitResponse)
def submit_task_endpoint(
    task_id: str,
    payload: TaskSubmitRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskSubmitResponse:
    _require_task_assignee(task_id, current_user.id)
    return submit_task(task_id, payload, actor_user_id=current_user.id)


@router.patch("/tasks/{task_id}", response_model=TaskUpdateResponse)
def update_task_endpoint(
    task_id: str,
    payload: TaskUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskUpdateResponse:
    _require_task_edit_access(task_id, current_user.id)
    normalized_payload = _normalize_task_update_payload(task_id, payload)
    return update_task(task_id, normalized_payload, actor_user_id=current_user.id)


@router.delete("/tasks/{task_id}", response_model=TaskDeleteResponse)
def delete_task_endpoint(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskDeleteResponse:
    _require_task_delete_access(task_id, current_user.id)
    return delete_task(task_id, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/answer", response_model=TaskAnswerResponse)
def answer_task_endpoint(
    task_id: str,
    payload: TaskAnswerRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskAnswerResponse:
    _require_task_assignee(task_id, current_user.id)
    return answer_task(task_id, payload)


@router.post("/tasks/{task_id}/retry", response_model=TaskRetryResponse)
def retry_task_endpoint(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskRetryResponse:
    _require_task_assignee(task_id, current_user.id)
    return retry_task(task_id, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/approve", response_model=TaskApproveResponse)
def approve_task_endpoint(
    task_id: str,
    payload: TaskApproveRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskApproveResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return approve_task(task_id, payload, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/request-changes", response_model=TaskRequestChangesResponse)
def request_changes_task_endpoint(
    task_id: str,
    payload: TaskRequestChangesRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskRequestChangesResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return request_changes_task(task_id, payload, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/close", response_model=TaskCloseResponse)
def close_task_endpoint(
    task_id: str,
    payload: TaskCloseRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskCloseResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return close_task(task_id, payload, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/cancel", response_model=TaskCancelResponse)
def cancel_task_endpoint(
    task_id: str,
    payload: TaskCancelRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskCancelResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return cancel_task(task_id, payload, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/reopen", response_model=TaskReopenResponse)
def reopen_task_endpoint(
    task_id: str,
    payload: TaskReopenRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskReopenResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return reopen_task(task_id, payload, actor_user_id=current_user.id)


@router.post("/tasks/{task_id}/delta-bonuses", response_model=TaskDeltaBonusResponse)
def delta_bonus_task_endpoint(
    task_id: str,
    payload: TaskDeltaBonusRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TaskDeltaBonusResponse:
    _require_task_sensitive_access(task_id, current_user.id)
    return grant_delta_bonus(task_id, payload, actor_user_id=current_user.id)


@router.get("/projects/{project_id}/tasks", response_model_exclude_none=True)
def list_project_tasks_endpoint(
    project_id: str,
    view: ProjectTaskView | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
) -> ProjectTaskListResponse | ProjectTaskReadListResponse:
    if view is not None:
        return list_project_tasks_by_view(project_id, view, current_user.id).model_dump(exclude_none=True)
    with get_db_session() as session:
        require_project_member(session, project_id, current_user.id)
    return list_project_tasks(project_id)


@router.get(
    "/projects/{project_id}/contribution",
    response_model=ContributionResponse,
)
def get_project_contribution_endpoint(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> ContributionResponse:
    with get_db_session() as session:
        require_project_member(session, project_id, current_user.id)
    return get_project_contribution(project_id)


def _require_task_project_member(task_id: str, user_id: str) -> None:
    project_id = _get_task_project_id(task_id)
    with get_db_session() as session:
        require_project_member(session, project_id, user_id)


def _require_task_sensitive_access(task_id: str, user_id: str) -> None:
    project_id = _get_task_project_id(task_id)
    with get_db_session() as session:
        require_sensitive_review_access(session, project_id, user_id)


def _require_task_edit_access(task_id: str, user_id: str) -> None:
    with get_db_session() as session:
        task_record = session.get(TaskRecord, task_id)
        if task_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        require_task_create_access(session, task_record.project_id, user_id)


def _require_task_delete_access(task_id: str, user_id: str) -> None:
    with get_db_session() as session:
        task_record = session.get(TaskRecord, task_id)
        if task_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        require_task_create_access(session, task_record.project_id, user_id)


def _require_task_assignee(task_id: str, user_id: str) -> None:
    with get_db_session() as session:
        task_record = session.get(TaskRecord, task_id)
        if task_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        require_project_member(session, task_record.project_id, user_id)
        if task_record.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="task assignee required")


def _get_task_project_id(task_id: str) -> str:
    with get_db_session() as session:
        task_record = session.get(TaskRecord, task_id)
        if task_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        return task_record.project_id


def _normalize_task_update_payload(task_id: str, payload: TaskUpdateRequest) -> TaskUpdateRequest:
    with get_db_session() as session:
        task_record = session.get(TaskRecord, task_id)
        if task_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
        assignee_member = get_project_member(session, task_record.project_id, payload.user_id)
        if assignee_member is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="assignee must be a project member")
        normalized_name = payload.user_name or assignee_member.display_name or payload.user_id
        return payload.model_copy(update={"user_name": normalized_name})
