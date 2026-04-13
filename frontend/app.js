const state = {
  tasks: [],
  selectedTaskId: null,
  taskListExpanded: false,
  loadingPhase: null,
  loadingTaskId: null,
  taskListMessage: "",
  isTaskListLoading: false,
  taskView: "my",
  projectRole: "",
  projectEntryLoaded: false,
  projectEntryMode: "empty",
  projectMembers: [],
  selectedAssigneeId: "",
  assigneeSearchQuery: "",
  taskFormMode: "create",
  editingTaskId: null,
  errorMessage: "",
  drafts: {},
  currentUser: null,
  isAuthenticated: false,
  isBootstrapped: false,
  projectEntryRequestId: 0,
  context: window.AppContext.bootstrap(),
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  bindEvents();
  initializeAuth();
  render();
});

function bindElements() {
  elements.workspaceLogoutButton = document.getElementById("workspace-logout-button");
  elements.contextProject = document.getElementById("context-project");
  elements.contextUserDisplay = document.getElementById("context-user-display");
  elements.contextView = document.getElementById("context-view");
  elements.contextViewTabs = document.getElementById("context-view-tabs");
  elements.contextSummary = document.getElementById("context-summary");
  elements.projectEntryMessage = document.getElementById("project-entry-message");
  elements.taskForm = document.getElementById("task-create-form");
  elements.taskAssigneeSearch = document.getElementById("task-assignee-search");
  elements.taskAssigneeResults = document.getElementById("task-assignee-results");
  elements.taskAssigneeSelected = document.getElementById("task-assignee-selected");
  elements.taskAssigneeMessage = document.getElementById("task-assignee-message");
  elements.titleInput = document.getElementById("title");
  elements.taskTypeInput = document.getElementById("task-type");
  elements.taskGoalInput = document.getElementById("task-goal");
  elements.taskWeightInput = document.getElementById("task-weight");
  elements.createMessage = document.getElementById("create-message");
  elements.taskFormModeInput = document.getElementById("task-form-mode");
  elements.taskFormSubmitButton = document.getElementById("task-form-submit-button");
  elements.taskFormDeleteButton = document.getElementById("task-form-delete-button");
  elements.taskCreateModalTitle = document.getElementById("task-create-modal-title");
  elements.taskCreateModalHelp = document.getElementById("task-create-modal-help");

  elements.taskList = document.getElementById("task-list");
  elements.taskListToggle = document.getElementById("task-list-toggle");
  elements.emptyTaskList = document.getElementById("empty-task-list");
  elements.detailEmpty = document.getElementById("detail-empty");
  elements.detailBody = document.getElementById("detail-body");
  elements.taskMeta = document.getElementById("task-meta");
  elements.statusText = document.getElementById("task-status");
  elements.taskStageTitle = document.getElementById("task-stage-title");
  elements.taskStatusBadge = document.getElementById("task-status-badge");
  elements.taskActionHint = document.getElementById("task-action-hint");
  elements.loadingSection = document.getElementById("loading-section");
  elements.loadingText = document.getElementById("loading-text");

  elements.submitSection = document.getElementById("submit-section");
  elements.contentInput = document.getElementById("content");
  elements.submitButton = document.getElementById("submit-button");

  elements.questionSection = document.getElementById("question-section");
  elements.aiQuestion = document.getElementById("ai-question");
  elements.answerInput = document.getElementById("user-answer");
  elements.answerButton = document.getElementById("answer-button");

  elements.reviewFeedbackSection = document.getElementById("review-feedback-section");
  elements.reviewFeedbackStatus = document.getElementById("review-feedback-status");
  elements.reviewFeedbackMessageWrap = document.getElementById("review-feedback-message-wrap");
  elements.reviewFeedbackMessage = document.getElementById("review-feedback-message");

  elements.resultSection = document.getElementById("result-section");
  elements.resultPolicyNote = document.getElementById("result-policy-note");
  elements.resultAiQuestion = document.getElementById("result-ai-question");
  elements.resultUserAnswer = document.getElementById("result-user-answer");
  elements.scoreMeta = document.getElementById("score-meta");
  elements.rawScoreRow = document.getElementById("raw-score-row");
  elements.rawScoreLabel = document.getElementById("raw-score-label");
  elements.weightedScoreRow = document.getElementById("weighted-score-row");
  elements.weightedScoreLabel = document.getElementById("weighted-score-label");
  elements.rawScore = document.getElementById("raw-score");
  elements.weightedScore = document.getElementById("weighted-score");
  elements.aiComment = document.getElementById("ai-comment");

  elements.managerReviewSection = document.getElementById("manager-review-section");
  elements.reviewMessageInput = document.getElementById("review-message-input");
  elements.deltaBonusInput = document.getElementById("delta-bonus-input");
  elements.approveButton = document.getElementById("approve-button");
  elements.requestChangesButton = document.getElementById("request-changes-button");
  elements.deltaBonusButton = document.getElementById("delta-bonus-button");
  elements.reviewActionMessage = document.getElementById("review-action-message");

  elements.errorSection = document.getElementById("error-section");
  elements.errorText = document.getElementById("error-text");
  elements.retryButton = document.getElementById("retry-button");
}

async function initializeContext() {
  renderContextOptions();
  ensureValidContext();
  syncContextUI();
  await loadProjectEntryOptions({ reloadTasks: false });
  if (state.projectEntryLoaded) {
    await loadProjectTasks();
  }
}

function bindEvents() {
  elements.contextProject.addEventListener("change", handleContextChange);
  elements.contextView.addEventListener("change", handleViewChange);
  elements.contextViewTabs?.addEventListener("click", handleViewTabClick);
  elements.workspaceLogoutButton.addEventListener("click", handleLogout);
  elements.taskForm.addEventListener("submit", handleCreateTask);
  document.addEventListener("task-create-modal-reset", resetTaskCreateModalState);
  elements.taskAssigneeSearch?.addEventListener("input", handleAssigneeSearchInput);
  elements.taskAssigneeResults?.addEventListener("click", handleAssigneeResultClick);
  elements.taskAssigneeSelected?.addEventListener("click", handleAssigneeSelectedClick);
  elements.submitButton.addEventListener("click", handleSubmitTask);
  elements.answerButton.addEventListener("click", handleAnswerTask);
  elements.retryButton.addEventListener("click", handleRetryTask);
  elements.approveButton.addEventListener("click", handleApproveTask);
  elements.requestChangesButton.addEventListener("click", handleRequestChanges);
  elements.deltaBonusButton.addEventListener("click", handleDeltaBonus);
  elements.contentInput.addEventListener("input", handleContentDraftChange);
  elements.answerInput.addEventListener("input", handleAnswerDraftChange);
  elements.taskList.addEventListener("click", handleSelectTask);
  elements.taskListToggle?.addEventListener("click", handleTaskListToggle);
  elements.taskFormDeleteButton?.addEventListener("click", handleDeleteTask);
}

async function initializeAuth() {
  const session = window.AuthApi.load();
  if (!session?.access_token) {
    redirectToLogin();
    return;
  }

  try {
    const user = await window.AuthApi.fetchCurrentUser();
    applyAuthenticatedUser(user);
    await initializeContext();
  } catch (error) {
    window.AuthApi.clear();
    window.AuthApi.redirectToLogin("index.html", "expired");
    return;
  } finally {
    state.isBootstrapped = true;
    render();
  }
}

async function handleLogout() {
  await window.AuthApi.logout();
  state.isAuthenticated = false;
  state.currentUser = null;
  state.tasks = [];
  state.selectedTaskId = null;
  window.location.href = window.AuthApi.buildLoginUrl("index.html", "logged_out");
}

function applyAuthenticatedUser(user) {
  state.currentUser = user;
  state.isAuthenticated = true;
  state.context = window.AppContext.bootstrap({
    projectId: state.context.projectId,
    userId: user.id,
  });
}

function redirectToLogin() {
  window.AuthApi.redirectToLogin("index.html", "auth_required");
}

function normalizeProjectId(value) {
  return value == null ? "" : String(value);
}

function getProjectId(project) {
  return normalizeProjectId(project?.project_id ?? project?.id);
}

function formatUserDisplay(user) {
  return window.AuthApi.getPreferredUserDisplay(user);
}

const TASK_VIEW_LABELS = {
  my: "내 작업",
  overview: "프로젝트 전체",
  "sensitive-review": "검토",
};

function getTaskViewLabel(view) {
  return TASK_VIEW_LABELS[view] || view || "프로젝트 전체";
}

function getMemberDisplayName(member) {
  const displayName = String(member?.display_name || "").trim();
  const email = String(member?.email || "").trim();
  const userId = String(member?.user_id || "").trim();
  return displayName || email || userId || "사용자 미확인";
}

function getMemberSubLabel(member) {
  const email = String(member?.email || "").trim();
  const role = String(member?.role || "").trim();
  return [email, role ? `project role: ${role}` : ""].filter(Boolean).join(" · ");
}

function getSelectedAssignee() {
  return state.projectMembers.find((member) => String(member.user_id) === String(state.selectedAssigneeId)) || null;
}

function getTaskAssigneeId(task) {
  return String(task?.client_user_id || task?.user_id || "");
}

function isTaskAssignee(task) {
  return Boolean(task && state.currentUser?.id && getTaskAssigneeId(task) === String(state.currentUser.id));
}

function renderContextOptions() {
  elements.contextProject.innerHTML = window.AppContext.options.projects
    .map(
      (project) =>
        `<option value="${escapeHtml(project.id)}">${escapeHtml(project.name)}</option>`,
    )
    .join("");

}

function ensureValidContext() {
  const projectOptionValues = Array.from(elements.contextProject.options)
    .map((option) => option.value)
    .filter(Boolean);

  if (!projectOptionValues.length) {
    state.context = {
      projectId: state.context.projectId || "",
      userId: state.currentUser?.id || state.context.userId,
    };
    return;
  }

  const fallbackProjectId = projectOptionValues[0] || window.AppContext.getDefaultContext().projectId;
  const projectId = state.context.projectId && projectOptionValues.includes(state.context.projectId)
    ? state.context.projectId
    : fallbackProjectId;
  const userId = state.currentUser?.id || state.context.userId;

  state.context = window.AppContext.bootstrap({
    projectId,
    userId,
  });
}

async function handleContextChange() {
  // 기획 반영: Workspace와 Dashboard가 같은 project/user 컨텍스트를 공유한다.
  state.context = window.AppContext.bootstrap({
    projectId: elements.contextProject.value,
    userId: state.currentUser?.id || state.context.userId,
  });
  clearError();
  resetAssigneeSelection();
  syncContextUI();
  await loadProjectEntryOptions({ reloadTasks: false });
  if (state.projectEntryLoaded) {
    await loadProjectTasks();
  }
}

function handleViewChange() {
  clearError();
  state.taskView = elements.contextView.value || "my";
  if (state.taskView === "sensitive-review" && !canUseSensitiveReview()) {
    state.taskView = "overview";
    setError("현재 role에서는 검토 화면에 접근할 수 없습니다.");
  }
  loadProjectTasks();
}

function handleViewTabClick(event) {
  const button = event.target.closest("[data-task-view]");
  if (!button || button.disabled) {
    return;
  }
  elements.contextView.value = button.dataset.taskView;
  handleViewChange();
}

function syncContextUI() {
  ensureValidContext();
  elements.contextProject.value = state.context.projectId;
  elements.contextView.value = state.taskView;
  state.projectRole = window.AppContext.getProjectRole(state.context.projectId);
  updateViewOptionsForRole();
  elements.contextView.value = state.taskView;
  updateViewTabs();
  const currentUserLabel = formatUserDisplay(state.currentUser);
  elements.contextUserDisplay.textContent = currentUserLabel;
  renderAssigneePicker();
  const contextMode = state.projectEntryLoaded ? "server API" : "no project selected";
  elements.contextSummary.textContent =
    `${window.AppContext.getProjectLabel(state.context.projectId)}에서 ${currentUserLabel} 기준 ${getTaskViewLabel(state.taskView)} 화면으로 작업을 확인합니다. role: ${state.projectRole || "none"} / context: ${contextMode}`;
}

function updateViewOptionsForRole() {
  const sensitiveOption = Array.from(elements.contextView.options)
    .find((option) => option.value === "sensitive-review");
  if (!sensitiveOption) {
    return;
  }

  sensitiveOption.hidden = !canUseSensitiveReview();
  sensitiveOption.disabled = !canUseSensitiveReview();
  if (!canUseSensitiveReview() && state.taskView === "sensitive-review") {
    state.taskView = "overview";
  }
}

function updateViewTabs() {
  if (!elements.contextViewTabs) {
    return;
  }

  elements.contextViewTabs.querySelectorAll("[data-task-view]").forEach((button) => {
    const view = button.dataset.taskView;
    const isSensitive = view === "sensitive-review";
    const isAllowed = !isSensitive || canUseSensitiveReview();
    button.hidden = !isAllowed;
    button.disabled = !isAllowed;
    button.classList.toggle("is-active", view === state.taskView);
    button.setAttribute("aria-pressed", view === state.taskView ? "true" : "false");
  });
}

function canUseSensitiveReview() {
  return state.projectRole === "owner" || state.projectRole === "manager";
}

function canManageTask(task) {
  return Boolean(task && task.status === "TODO" && canUseSensitiveReview());
}

function isMyView() {
  return state.taskView === "my";
}

function isOverviewView() {
  return state.taskView === "overview";
}

function isSensitiveReviewView() {
  return state.taskView === "sensitive-review";
}

function isTaskApproved(task) {
  return Boolean(
    task
    && (
      task.work_status === "APPROVED"
      || task.score_lock_status === "LOCKED"
      || task.score_lock_status === "LOCKED_WITH_BONUS"
      || task.approved_version_no
    ),
  );
}

function canShowResultDetails() {
  return isMyView() || isSensitiveReviewView();
}

function getFinalScore(task) {
  if (!task) {
    return null;
  }
  if (task.final_score !== null && task.final_score !== undefined) {
    const apiFinalScore = Number(task.final_score);
    return Number.isFinite(apiFinalScore) ? apiFinalScore : null;
  }
  if (!isTaskApproved(task)) {
    return null;
  }
  const lockedMainScore = Number(task.locked_main_score ?? 0);
  const totalDeltaBonus = Number(task.total_delta_bonus ?? 0);
  if (!Number.isFinite(lockedMainScore) || !Number.isFinite(totalDeltaBonus)) {
    return null;
  }
  return lockedMainScore + totalDeltaBonus;
}

function getSelectedTask() {
  return state.tasks.find((task) => task.task_id === state.selectedTaskId) || null;
}

function isSelectedTaskLoading() {
  const task = getSelectedTask();
  return Boolean(task && state.loadingTaskId === task.task_id && state.loadingPhase);
}

function updateTask(taskId, updates) {
  state.tasks = state.tasks.map((task) =>
    task.task_id === taskId ? normalizeTask({ ...task, ...updates }) : task,
  );
}

async function loadProjectTasks(selectedTaskId = state.selectedTaskId) {
  state.taskListExpanded = false;
  ensureValidContext();
  if (!state.projectEntryLoaded || !state.context.projectId) {
    state.tasks = [];
    state.selectedTaskId = null;
    state.taskListMessage = "현재 선택 가능한 실제 프로젝트가 없습니다. Project Entry에서 프로젝트를 선택해 주세요.";
    render();
    return;
  }
  state.isTaskListLoading = true;
  state.taskListMessage = state.projectEntryLoaded
    ? `${getTaskViewLabel(state.taskView)} 화면으로 서버 프로젝트 task를 불러오고 있습니다.`
    : "현재 선택 가능한 실제 프로젝트가 없습니다.";
  render();

  try {
    const response = state.projectEntryLoaded
      ? await window.TaskApi.fetchProjectTasksByView(
        state.context.projectId,
        state.taskView,
      )
      : await window.TaskApi.fetchProjectTasks(state.context.projectId);
    state.tasks = (response.tasks || []).map(normalizeTask);
    state.selectedTaskId = resolveSelectedTaskId(state.tasks, selectedTaskId);
    state.taskListExpanded = shouldAutoExpandList(state.tasks, state.selectedTaskId, "task_id");
    state.taskListMessage = state.tasks.length
      ? ""
      : state.projectEntryLoaded
        ? `${getTaskViewLabel(state.taskView)} 화면에 표시할 task가 없습니다. owner/manager로 task를 생성하거나 보기를 전환해 주세요.`
        : "현재 선택 가능한 실제 프로젝트가 없습니다. Project Entry에서 프로젝트를 선택해 주세요.";
  } catch (error) {
    state.tasks = [];
    state.selectedTaskId = null;
    state.taskListMessage = "작업 목록을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
    setError(error.message);
  } finally {
    state.isTaskListLoading = false;
    render();
  }
}

async function loadProjectEntryOptions({ reloadTasks = true } = {}) {
  const requestId = state.projectEntryRequestId + 1;
  state.projectEntryRequestId = requestId;

  try {
    const preferredProjectId = normalizeProjectId(
      state.context.projectId || window.AppContext.load().projectId,
    );
    const teamsResponse = await window.TaskApi.fetchTeams();
    if (requestId !== state.projectEntryRequestId) {
      return;
    }
    const teams = teamsResponse.teams || [];
    window.AppContext.updateOptions({ teams });
    if (!teams.length) {
      window.AppContext.updateOptions({ teams, projects: [] });
      state.context = window.AppContext.save({
        projectId: "",
        userId: state.currentUser?.id || state.context.userId,
      });
      state.projectEntryLoaded = false;
      state.projectEntryMode = "empty";
      state.tasks = [];
      state.selectedTaskId = null;
      elements.contextProject.innerHTML = '<option value="">프로젝트 없음</option>';
      elements.contextProject.disabled = true;
      state.taskListMessage = "로그인 사용자 기준 접근 가능한 팀/프로젝트가 없습니다. 팀과 프로젝트를 먼저 생성해 주세요.";
      elements.projectEntryMessage.innerHTML = '현재 로그인 사용자로 조회 가능한 팀이 없습니다. <a class="context-link" href="./projects.html">Project Entry</a>에서 팀/프로젝트를 생성해 주세요.';
      return;
    }

    const projectResponses = await Promise.all(
      teams.map((team) => window.TaskApi.fetchTeamProjects(team.team_id)),
    );
    if (requestId !== state.projectEntryRequestId) {
      return;
    }
    const projects = projectResponses.flatMap((response) => response.projects || []);

    if (projects.length) {
      window.AppContext.updateOptions({ teams, projects });
      if (preferredProjectId && projects.some((project) => getProjectId(project) === preferredProjectId)) {
        state.context = window.AppContext.bootstrap({
          projectId: preferredProjectId,
          userId: state.currentUser?.id || state.context.userId,
        });
      }
      elements.contextProject.disabled = false;
      renderContextOptions();
      ensureValidContext();
      state.projectEntryLoaded = true;
      state.projectEntryMode = "server";
      await loadProjectMembers();
      syncContextUI();
      elements.projectEntryMessage.textContent = `${teams.length}개 팀, ${projects.length}개 프로젝트를 서버에서 불러왔습니다. 실제 API 컨텍스트를 사용합니다.`;
      if (reloadTasks) {
        await loadProjectTasks();
      }
    } else {
      window.AppContext.updateOptions({ teams, projects: [] });
      state.context = window.AppContext.save({
        projectId: "",
        userId: state.currentUser?.id || state.context.userId,
      });
      state.projectEntryLoaded = false;
      state.projectEntryMode = "empty";
      elements.contextProject.innerHTML = '<option value="">프로젝트 없음</option>';
      elements.contextProject.disabled = true;
      syncContextUI();
      state.tasks = [];
      state.selectedTaskId = null;
      state.taskListMessage = "로그인 사용자 기준 접근 가능한 프로젝트가 없습니다. 프로젝트 생성 또는 멤버 배정이 필요합니다.";
      elements.projectEntryMessage.innerHTML = '접근 가능한 프로젝트가 없습니다. <a class="context-link" href="./projects.html">Project Entry</a>에서 프로젝트 생성 또는 멤버 배정을 진행해 주세요.';
    }
  } catch (error) {
    state.projectEntryLoaded = false;
    state.projectEntryMode = "error";
    elements.contextProject.innerHTML = '<option value="">프로젝트 없음</option>';
    elements.contextProject.disabled = true;
    state.tasks = [];
    state.selectedTaskId = null;
    state.taskListMessage = "팀/프로젝트 entry API를 불러오지 못했습니다. 로그인 세션과 서버 상태를 확인해 주세요.";
    elements.projectEntryMessage.textContent = "팀/프로젝트 entry API를 불러오지 못했습니다. 로그인 세션과 서버 상태를 확인해 주세요.";
  }
}

async function loadProjectMembers() {
  if (!state.projectEntryLoaded || !state.context.projectId) {
    state.projectMembers = [];
    resetAssigneeSelection();
    renderAssigneePicker();
    return;
  }

  try {
    const response = await window.TaskApi.fetchProjectMembers(
      state.context.projectId,
    );
    state.projectMembers = response.members || [];
    if (state.selectedAssigneeId && !state.projectMembers.some((member) => String(member.user_id) === String(state.selectedAssigneeId))) {
      resetAssigneeSelection();
    }
    const currentMember = state.projectMembers.find((member) => String(member.user_id) === String(state.context.userId));
    state.projectRole = currentMember?.role || window.AppContext.getProjectRole(state.context.projectId);
  } catch (error) {
    state.projectMembers = [];
    resetAssigneeSelection();
  }
  renderAssigneePicker();
}

async function handleCreateTask(event) {
  event.preventDefault();
  clearError();
  ensureValidContext();

  if (state.taskFormMode === "edit") {
    await handleUpdateTask();
    return;
  }

  const formPayload = buildTaskFormPayload();
  const payload = formPayload
    ? {
      project_id: state.context.projectId,
      ...formPayload,
    }
    : null;

  if (!payload || !payload.project_id || !payload.title || !payload.task_type || !payload.task_goal || !payload.user_id || !getSelectedAssignee()) {
    setError("작업 등록에 필요한 항목과 담당자를 모두 입력해 주세요.");
    setCreateMessage("");
    render();
    return;
  }

  setCreateMessage("작업을 등록하고 있습니다.");

  try {
    if (state.projectEntryLoaded && !canUseSensitiveReview()) {
      throw new Error("task 생성은 owner/manager role에서만 가능합니다.");
    }
    const task = normalizeTask(
      state.projectEntryLoaded
        ? await window.TaskApi.createProjectTask(state.context.projectId, payload)
        : await window.TaskApi.createTask(payload),
    );
    state.selectedTaskId = task.task_id;
    setCreateMessage("작업이 등록되었습니다.");
    resetAssigneeSelection();
    await loadProjectTasks(task.task_id);
  } catch (error) {
    setError(error.message);
    setCreateMessage("");
    render();
  }
}

async function handleUpdateTask() {
  const task = state.tasks.find((item) => item.task_id === state.editingTaskId) || getSelectedTask();
  const payload = buildTaskFormPayload();

  if (!task || !canManageTask(task)) {
    setError("only TODO task can be edited");
    setCreateMessage("");
    render();
    return;
  }

  if (!payload) {
    setError("작업 저장에 필요한 항목과 담당자를 모두 입력해 주세요.");
    setCreateMessage("");
    render();
    return;
  }

  setCreateMessage("작업을 저장하고 있습니다.");

  try {
    await window.TaskApi.updateTask(task.task_id, payload);
    setCreateMessage("작업이 저장되었습니다.");
    await loadProjectTasks(task.task_id);
  } catch (error) {
    setError(error.message);
    setCreateMessage("");
    render();
  }
}

function buildTaskFormPayload() {
  const payload = {
    user_id: state.selectedAssigneeId,
    user_name: getMemberDisplayName(getSelectedAssignee()),
    title: elements.titleInput.value.trim(),
    task_type: elements.taskTypeInput.value.trim(),
    task_goal: elements.taskGoalInput.value.trim(),
    task_weight: Number(elements.taskWeightInput.value),
  };

  if (!payload.title || !payload.task_type || !payload.task_goal || !payload.user_id || !getSelectedAssignee()) {
    return null;
  }

  return payload;
}

function resetAssigneeSelection() {
  state.selectedAssigneeId = "";
  state.assigneeSearchQuery = "";
  if (elements.taskAssigneeSearch) {
    elements.taskAssigneeSearch.value = "";
  }
}

function resetTaskCreateModalState() {
  state.taskFormMode = "create";
  state.editingTaskId = null;
  resetAssigneeSelection();
  if (elements.taskForm) {
    elements.taskForm.reset();
  }
  if (elements.taskFormModeInput) {
    elements.taskFormModeInput.value = "create";
  }
  if (elements.taskFormSubmitButton) {
    elements.taskFormSubmitButton.textContent = "작업 등록";
  }
  if (elements.taskFormDeleteButton) {
    elements.taskFormDeleteButton.hidden = true;
  }
  if (elements.taskCreateModalTitle) {
    elements.taskCreateModalTitle.textContent = "Task 생성";
  }
  if (elements.taskCreateModalHelp) {
    elements.taskCreateModalHelp.textContent = "현재 프로젝트 기준으로 task title, type, goal과 담당자를 지정합니다.";
  }
  if (elements.createMessage) {
    setCreateMessage("");
  }
  renderAssigneePicker();
}

function handleOpenTaskEditModal(taskId = state.selectedTaskId) {
  const task = state.tasks.find((item) => item.task_id === String(taskId)) || getSelectedTask();
  const modal = document.getElementById("task-create-modal");
  if (!task || !canManageTask(task) || !modal) {
    return;
  }

  state.taskFormMode = "edit";
  state.editingTaskId = task.task_id;
  state.selectedAssigneeId = getTaskAssigneeId(task);
  state.assigneeSearchQuery = "";
  if (elements.taskAssigneeSearch) {
    elements.taskAssigneeSearch.value = "";
  }
  if (elements.titleInput) {
    elements.titleInput.value = task.title || "";
  }
  if (elements.taskTypeInput) {
    elements.taskTypeInput.value = task.task_type || "";
  }
  if (elements.taskGoalInput) {
    elements.taskGoalInput.value = task.task_goal || "";
  }
  if (elements.taskWeightInput) {
    elements.taskWeightInput.value = String(task.task_weight || 2);
  }
  if (elements.taskFormModeInput) {
    elements.taskFormModeInput.value = "edit";
  }
  if (elements.taskFormSubmitButton) {
    elements.taskFormSubmitButton.textContent = "저장";
  }
  if (elements.taskFormDeleteButton) {
    elements.taskFormDeleteButton.hidden = false;
  }
  if (elements.taskCreateModalTitle) {
    elements.taskCreateModalTitle.textContent = "Task 편집";
  }
  if (elements.taskCreateModalHelp) {
    elements.taskCreateModalHelp.textContent = "TODO 상태 task의 title, type, goal, 담당자, 중요도를 수정할 수 있습니다.";
  }
  setCreateMessage("");
  renderAssigneePicker();
  modal.hidden = false;
}

async function handleDeleteTask() {
  const task = state.tasks.find((item) => item.task_id === state.editingTaskId) || getSelectedTask();
  if (!task || !canManageTask(task)) {
    setError("only TODO task can be deleted");
    setCreateMessage("");
    render();
    return;
  }

  const confirmed = window.confirm("TODO 상태 task를 삭제할까요? 제출 이후 task는 평가/검토 이력 보존을 위해 삭제할 수 없습니다.");
  if (!confirmed) {
    return;
  }

  clearError();
  setCreateMessage("작업을 삭제하고 있습니다.");

  try {
    await window.TaskApi.deleteTask(task.task_id);
    delete state.drafts[task.task_id];
    if (state.selectedTaskId === task.task_id) {
      state.selectedTaskId = null;
    }
    setCreateMessage("작업이 삭제되었습니다.");
    await loadProjectTasks(null);
  } catch (error) {
    setError(error.message);
    setCreateMessage("");
    render();
  }
}

function handleAssigneeSearchInput(event) {
  state.assigneeSearchQuery = event.target.value;
  renderAssigneePicker();
}

function handleAssigneeResultClick(event) {
  const button = event.target.closest("[data-assignee-id]");
  if (!button) {
    return;
  }
  state.selectedAssigneeId = button.dataset.assigneeId;
  state.assigneeSearchQuery = "";
  if (elements.taskAssigneeSearch) {
    elements.taskAssigneeSearch.value = "";
  }
  renderAssigneePicker();
}

function handleAssigneeSelectedClick(event) {
  if (!event.target.closest("[data-clear-assignee]")) {
    return;
  }
  resetAssigneeSelection();
  renderAssigneePicker();
}

function renderAssigneePicker() {
  const selected = getSelectedAssignee();
  const modeLabel = state.taskFormMode === "edit" ? "수정" : "생성";

  if (elements.taskAssigneeSelected) {
    elements.taskAssigneeSelected.innerHTML = selected
      ? `
        <div class="assignee-selected-row">
          <span>
            <strong>${escapeHtml(getMemberDisplayName(selected))}</strong>
            <small>${escapeHtml(getMemberSubLabel(selected) || selected.user_id)}</small>
          </span>
          <button type="button" data-clear-assignee="true">교체</button>
        </div>
      `
      : `<p class="field-help">현재 프로젝트 멤버 중 담당자 1명을 선택해야 task를 ${escapeHtml(modeLabel)}할 수 있습니다.</p>`;
  }

  if (elements.taskAssigneeMessage) {
    elements.taskAssigneeMessage.textContent = state.projectMembers.length
      ? "이름 또는 email로 현재 프로젝트 멤버를 검색합니다."
      : "현재 프로젝트 멤버를 불러오지 못했습니다.";
  }

  if (!elements.taskAssigneeResults) {
    return;
  }

  const query = String(state.assigneeSearchQuery || "").trim().toLowerCase();
  const candidates = state.projectMembers
    .filter((member) => String(member.user_id) !== String(state.selectedAssigneeId))
    .filter((member) => {
      if (!query) {
        return true;
      }
      return [
        member.display_name,
        member.email,
        member.user_id,
      ].some((value) => String(value || "").toLowerCase().includes(query));
    })
    .slice(0, 8);

  elements.taskAssigneeResults.innerHTML = candidates.length
    ? candidates.map((member) => `
      <button type="button" class="assignee-result-row" data-assignee-id="${escapeHtml(member.user_id)}">
        <span>
          <strong>${escapeHtml(getMemberDisplayName(member))}</strong>
          <small>${escapeHtml(getMemberSubLabel(member) || member.user_id)}</small>
        </span>
        <span>선택</span>
      </button>
    `).join("")
    : '<p class="field-help">선택 가능한 프로젝트 멤버가 없습니다.</p>';
}

async function handleApproveTask() {
  const task = getSelectedTask();
  if (!task || !canUseSensitiveReview()) {
    return;
  }
  await runReviewAction(() => window.TaskApi.approveTask(task.task_id, {
    comment: elements.reviewMessageInput.value.trim() || "approved from manager review",
  }), "승인되었습니다.");
}

async function handleRequestChanges() {
  const task = getSelectedTask();
  if (!task || !canUseSensitiveReview()) {
    return;
  }
  if (isTaskApproved(task)) {
    setError("승인된 작업에는 보완 요청을 다시 등록할 수 없습니다.");
    render();
    return;
  }
  await runReviewAction(() => window.TaskApi.requestTaskChanges(task.task_id, {
    reason: elements.reviewMessageInput.value.trim() || "changes requested from manager review",
  }), "보완 요청이 등록되었습니다.");
}

async function handleDeltaBonus() {
  const task = getSelectedTask();
  if (!task || !canUseSensitiveReview()) {
    return;
  }
  await runReviewAction(() => window.TaskApi.grantDeltaBonus(task.task_id, {
    bonus_points: Number(elements.deltaBonusInput.value || 0.5),
    reason_code: "MANAGER_REVIEW",
    reason_detail: elements.reviewMessageInput.value.trim() || "manager review delta bonus",
  }), "delta bonus가 지급되었습니다.");
}

async function runReviewAction(action, successMessage) {
  clearError();
  elements.reviewActionMessage.textContent = "요청을 처리하고 있습니다.";
  try {
    await action();
    elements.reviewActionMessage.textContent = successMessage;
    await loadProjectTasks(state.selectedTaskId);
  } catch (error) {
    elements.reviewActionMessage.textContent = "";
    setError(error.message);
    render();
  }
}

async function handleSubmitTask() {
  const task = getSelectedTask();
  if (!task || task.status !== "TODO") {
    return;
  }
  if (!isTaskAssignee(task)) {
    setError("담당자만 작업 결과를 제출할 수 있습니다.");
    render();
    return;
  }

  const content = elements.contentInput.value.trim();
  if (!content) {
    setError("제출할 작업 결과를 입력해 주세요.");
    render();
    return;
  }

  clearError();
  updateTask(task.task_id, { content });
  state.loadingPhase = "GENERATING_Q";
  state.loadingTaskId = task.task_id;
  render();

  try {
    const response = await window.TaskApi.submitTask(task.task_id, {
      content,
    });
    updateTask(task.task_id, {
      ...response,
      content: response.content,
    });
    clearDraftValue(task.task_id, "content");
    await loadProjectTasks(task.task_id);
  } catch (error) {
    updateTask(task.task_id, {
      status: "FAILED",
    });
    setError(error.message);
  } finally {
    state.loadingPhase = null;
    state.loadingTaskId = null;
    render();
  }
}

async function handleAnswerTask() {
  const task = getSelectedTask();
  if (!task || task.status !== "AWAITING_A") {
    return;
  }
  if (!isTaskAssignee(task)) {
    setError("담당자만 AI 질문에 답변할 수 있습니다.");
    render();
    return;
  }

  const userAnswer = elements.answerInput.value.trim();
  if (!userAnswer) {
    setError("AI 질문에 대한 답변을 입력해 주세요.");
    render();
    return;
  }

  clearError();
  updateTask(task.task_id, { user_answer: userAnswer });
  state.loadingPhase = "SCORING";
  state.loadingTaskId = task.task_id;
  render();

  try {
    const response = await window.TaskApi.answerTask(task.task_id, {
      user_answer: userAnswer,
    });
    updateTask(task.task_id, {
      ...response,
      user_answer: response.user_answer,
    });
    clearDraftValue(task.task_id, "user_answer");
    await loadProjectTasks(task.task_id);
  } catch (error) {
    updateTask(task.task_id, {
      status: "FAILED",
      user_answer: userAnswer,
    });
    setError(error.message);
  } finally {
    state.loadingPhase = null;
    state.loadingTaskId = null;
    render();
  }
}

async function handleRetryTask() {
  const task = getSelectedTask();
  if (!task || task.status !== "FAILED") {
    return;
  }
  if (!isTaskAssignee(task)) {
    setError("담당자만 실패한 작업을 다시 시도할 수 있습니다.");
    render();
    return;
  }

  clearError();
  state.loadingTaskId = task.task_id;
  elements.retryButton.disabled = true;

  try {
    const response = await window.TaskApi.retryTask(task.task_id);
    updateTask(task.task_id, response);
    clearDraftValue(task.task_id, "user_answer");
    await loadProjectTasks(task.task_id);
  } catch (error) {
    setError(error.message);
  } finally {
    state.loadingTaskId = null;
    elements.retryButton.disabled = false;
    render();
  }
}

function handleContentDraftChange(event) {
  const task = getSelectedTask();
  if (!task) {
    return;
  }

  setDraftValue(task.task_id, "content", event.target.value);
  updateTask(task.task_id, { content: event.target.value });
  renderTaskList();
}

function handleAnswerDraftChange(event) {
  const task = getSelectedTask();
  if (!task) {
    return;
  }

  setDraftValue(task.task_id, "user_answer", event.target.value);
  updateTask(task.task_id, { user_answer: event.target.value });
  renderTaskList();
}

function handleSelectTask(event) {
  const editTrigger = event.target.closest("[data-task-edit]");
  if (editTrigger) {
    event.preventDefault();
    event.stopPropagation();
    handleOpenTaskEditModal(editTrigger.dataset.taskEdit);
    return;
  }

  const button = event.target.closest("[data-task-id]");
  if (!button) {
    return;
  }

  state.selectedTaskId = button.dataset.taskId;
  state.taskListExpanded = state.taskListExpanded || shouldAutoExpandList(state.tasks, state.selectedTaskId, "task_id");
  clearError();
  clearReviewActionMessage();
  render();
}

function normalizeTask(task) {
  const draft = state.drafts[task.task_id] || {};

  return {
    ...task,
    client_user_id: task.client_user_id || task.user_id || "",
    client_user_name: task.client_user_name || task.user_name || "",
    content: draft.content ?? task.content ?? task.submission_content ?? "",
    ai_question: task.ai_question || "",
    user_answer: draft.user_answer ?? task.user_answer ?? "",
    raw_score: task.raw_score ?? null,
    weighted_score: task.weighted_score ?? null,
    ai_comment: task.ai_comment || "",
    final_score: task.final_score ?? null,
    locked_main_score: task.locked_main_score ?? null,
    total_delta_bonus: task.total_delta_bonus ?? null,
    latest_review_feedback_type: task.latest_review_feedback_type || null,
    latest_review_feedback_reason: task.latest_review_feedback_reason || null,
    latest_review_feedback_at: task.latest_review_feedback_at || null,
    bonus_logs: task.bonus_logs || [],
    activity_logs: task.activity_logs || [],
    failed_stage: task.failed_stage || null,
    error_message: task.error_message || "",
    created_at: task.created_at || "",
    updated_at: task.updated_at || "",
  };
}

function resolveSelectedTaskId(tasks, preferredTaskId) {
  if (!tasks.length) {
    return null;
  }

  if (preferredTaskId && tasks.some((task) => task.task_id === preferredTaskId)) {
    return preferredTaskId;
  }

  return tasks[0].task_id;
}

function setDraftValue(taskId, field, value) {
  state.drafts[taskId] = {
    ...(state.drafts[taskId] || {}),
    [field]: value,
  };
}

function clearDraftValue(taskId, field) {
  if (!state.drafts[taskId]) {
    return;
  }

  const nextDraft = { ...state.drafts[taskId] };
  delete nextDraft[field];

  if (Object.keys(nextDraft).length === 0) {
    delete state.drafts[taskId];
    return;
  }

  state.drafts[taskId] = nextDraft;
}

function setTextContent(element, value) {
  if (element) {
    element.textContent = value;
  }
}

function setElementClassName(element, value) {
  if (element) {
    element.className = value;
  }
}

function getStatusPresentation(status) {
  switch (status) {
    case "TODO":
      return {
        stageTitle: "제출 대기",
        actionLabel: "제출 대기",
        actionHint: "작업 결과를 정리한 뒤 결과 제출을 진행해 주세요.",
        note: "결과를 제출하면 AI 검증 질문 생성 단계로 넘어갑니다.",
      };
    case "GENERATING_Q":
      return {
        stageTitle: "질문 생성 중",
        actionLabel: "질문 생성 중",
        actionHint: "AI가 제출 내용을 바탕으로 검증 질문을 준비하고 있습니다.",
        note: "질문이 준비되면 바로 답변 단계로 이어집니다.",
      };
    case "AWAITING_A":
      return {
        stageTitle: "답변 필요",
        actionLabel: "답변 필요",
        actionHint: "AI 질문을 확인하고 실제 수행 내용을 중심으로 답변해 주세요.",
        note: "답변을 제출하면 AI가 채점과 코멘트 작성을 진행합니다.",
      };
    case "SCORING":
      return {
        stageTitle: "채점 중",
        actionLabel: "채점 중",
        actionHint: "제출한 답변을 AI가 평가하고 있습니다.",
        note: "점수와 코멘트가 정리되면 결과 화면으로 전환됩니다.",
      };
    case "DONE":
      return {
        stageTitle: "채점 완료",
        actionLabel: "채점 완료",
        actionHint: "최종 점수와 AI 코멘트를 확인할 수 있습니다.",
        note: "평가가 완료된 작업으로, 결과 확인 중심의 상태입니다.",
      };
    case "FAILED":
      return {
        stageTitle: "재시도 필요",
        actionLabel: "재시도 필요",
        actionHint: "처리 중 문제가 발생했습니다. 안내 문구를 확인한 뒤 다시 시도해 주세요.",
        note: "현재 정책상 FAILED 상태에서만 다시 시도할 수 있습니다.",
      };
    default:
      return {
        stageTitle: status,
        actionLabel: status,
        actionHint: "현재 상태를 확인해 주세요.",
        note: "상세 상태를 기준으로 다음 행동을 판단합니다.",
      };
  }
}

function getTaskNextAction(task, statusInfo, canPerformTaskAction, canReviewTask) {
  if (isSensitiveReviewView()) {
    if (canReviewTask) {
      return "완료된 작업입니다. 검토 결과를 반영할 수 있습니다.";
    }
    if (task.status !== "DONE") {
      return "담당자가 작업을 완료한 뒤 검토할 수 있습니다.";
    }
  }

  return canPerformTaskAction || task.status === "DONE"
    ? statusInfo.note
    : "담당자가 수행할 수 있습니다.";
}

function renderResultVisibility(task) {
  const isApproved = isTaskApproved(task);
  const finalScore = getFinalScore(task);

  elements.rawScoreRow.hidden = !isSensitiveReviewView();
  elements.weightedScoreRow.hidden = isMyView() ? !isApproved : false;
  elements.scoreMeta.hidden = isMyView() ? !isApproved : false;
  elements.rawScoreLabel.textContent = "raw score";
  elements.weightedScoreLabel.textContent = isMyView() ? "최종 점수" : "weighted score";

  if (isMyView()) {
    elements.resultPolicyNote.textContent = isApproved
      ? "최종 승인된 작업입니다. 사용자에게는 최종 점수만 공개됩니다."
      : "검토 중입니다. 최종 승인 후 점수가 공개됩니다.";
    elements.rawScore.textContent = "-";
    elements.weightedScore.textContent = finalScore === null ? "-" : `${formatScore(finalScore)}점`;
    return;
  }

  if (isSensitiveReviewView()) {
    elements.resultPolicyNote.textContent = "검토에서는 manager/owner용 상세 평가 정보와 운영 로그를 함께 확인합니다.";
    elements.rawScore.textContent = task.raw_score ?? "-";
    elements.weightedScore.textContent = task.weighted_score ?? "응답 누락";
    return;
  }

  elements.resultPolicyNote.textContent = "";
  elements.rawScore.textContent = "-";
  elements.weightedScore.textContent = "-";
}

function getLatestReviewFeedback(task) {
  if (!isMyView()) {
    return null;
  }

  if (task?.latest_review_feedback_type || task?.latest_review_feedback_reason) {
    return {
      status: task.latest_review_feedback_type === "changes_requested" ? "보완 요청" : "승인 완료",
      message: String(task.latest_review_feedback_reason || "").trim(),
      at: task.latest_review_feedback_at || null,
    };
  }

  const logs = Array.isArray(task?.activity_logs) ? task.activity_logs : [];
  const latestReviewLog = [...logs]
    .reverse()
    .find((log) => log?.action_type === "REQUEST_CHANGES" || log?.action_type === "APPROVE");

  if (!latestReviewLog) {
    return null;
  }

  const metadata = parseActivityMetadata(latestReviewLog.metadata);
  if (latestReviewLog.action_type === "REQUEST_CHANGES") {
    return {
      status: "보완 요청",
      message: String(metadata.reason || "").trim(),
      at: latestReviewLog.created_at || null,
    };
  }

  return {
    status: "승인 완료",
    message: String(metadata.comment || "").trim(),
    at: latestReviewLog.created_at || null,
  };
}

function parseActivityMetadata(metadata) {
  if (!metadata) {
    return {};
  }

  if (typeof metadata === "object") {
    return metadata;
  }

  try {
    return JSON.parse(metadata);
  } catch (error) {
    return {};
  }
}

function renderReviewFeedback(task) {
  const feedback = getLatestReviewFeedback(task);
  const shouldShow = Boolean(feedback);

  elements.reviewFeedbackSection.hidden = !shouldShow;
  elements.reviewFeedbackMessageWrap.hidden = true;
  elements.reviewFeedbackStatus.textContent = "-";
  elements.reviewFeedbackMessage.textContent = "-";

  if (!shouldShow) {
    return;
  }

  elements.reviewFeedbackStatus.textContent = feedback.status;
  if (feedback.message) {
    elements.reviewFeedbackMessageWrap.hidden = false;
    elements.reviewFeedbackMessage.textContent = feedback.message;
  }
}

function render() {
  if (!state.isAuthenticated || !state.isBootstrapped) {
    return;
  }

  const task = getSelectedTask();
  const isLoading = isSelectedTaskLoading();
  const currentStatus = task ? (isLoading ? state.loadingPhase : task.status) : "-";
  const isGenerating = isLoading && state.loadingPhase === "GENERATING_Q";
  const isScoring = isLoading && state.loadingPhase === "SCORING";
  const statusInfo = task ? getStatusPresentation(currentStatus) : null;
  const canPerformTaskAction = task ? isTaskAssignee(task) : false;
  const canReviewTask = task ? canUseSensitiveReview() && isSensitiveReviewView() && task.status === "DONE" && !isLoading : false;

  syncContextUI();
  renderTaskList();

  elements.emptyTaskList.hidden = state.tasks.length > 0;
  elements.emptyTaskList.textContent = state.taskListMessage || "생성된 task가 아직 없습니다.";
  elements.detailEmpty.hidden = Boolean(task);
  elements.detailBody.hidden = !task;

  if (!task) {
    setTextContent(elements.statusText, "-");
    setTextContent(elements.taskStageTitle, "-");
    setTextContent(elements.taskStatusBadge, "-");
    setElementClassName(elements.taskStatusBadge, "status-badge");
    setTextContent(elements.taskActionHint, "-");
    elements.taskMeta.innerHTML = "";
    elements.aiQuestion.textContent = "-";
    elements.reviewFeedbackSection.hidden = true;
    elements.reviewFeedbackStatus.textContent = "-";
    elements.reviewFeedbackMessageWrap.hidden = true;
    elements.reviewFeedbackMessage.textContent = "-";
    elements.resultPolicyNote.textContent = "";
    elements.resultAiQuestion.textContent = "-";
    elements.resultUserAnswer.textContent = "-";
    elements.scoreMeta.hidden = false;
    elements.rawScoreRow.hidden = false;
    elements.weightedScoreRow.hidden = false;
    elements.rawScoreLabel.textContent = "raw score";
    elements.weightedScoreLabel.textContent = "weighted score";
    elements.rawScore.textContent = "-";
    elements.weightedScore.textContent = "-";
    elements.aiComment.textContent = "-";
    elements.contentInput.value = "";
    elements.answerInput.value = "";
    elements.loadingSection.hidden = true;
    elements.submitSection.hidden = true;
    elements.questionSection.hidden = true;
    elements.resultSection.hidden = true;
    elements.managerReviewSection.hidden = true;
    elements.errorSection.hidden = true;
    elements.errorText.textContent = state.errorMessage || "요청 처리 중 문제가 발생했습니다.";
    elements.requestChangesButton.disabled = false;
    elements.requestChangesButton.title = "";
    return;
  }

  setTextContent(elements.statusText, currentStatus);
  setTextContent(elements.taskStageTitle, statusInfo.stageTitle);
  setTextContent(elements.taskStatusBadge, currentStatus);
  setElementClassName(elements.taskStatusBadge, `status-badge status-${currentStatus.toLowerCase()}`);
  setTextContent(
    elements.taskActionHint,
    canPerformTaskAction || task.status === "DONE"
      ? statusInfo.actionHint
      : "담당자가 아닌 task는 읽기 전용으로 확인합니다.",
  );
  elements.loadingSection.hidden = !(isGenerating || isScoring);
  elements.loadingText.textContent = isGenerating
    ? "AI가 제출 내용을 바탕으로 검증 질문을 생성하고 있습니다."
    : isScoring
      ? "AI가 답변을 검토하고 점수와 코멘트를 정리하고 있습니다."
      : "";

  elements.taskMeta.innerHTML = `
    <div><strong>담당자</strong>: ${escapeHtml(task.client_user_name || "-")}</div>
    <div><strong>title</strong>: ${escapeHtml(task.title)}</div>
    <div><strong>task_type</strong>: ${escapeHtml(task.task_type)}</div>
    <div><strong>task_goal</strong>: ${escapeHtml(task.task_goal)}</div>
    <div><strong>status</strong>: ${escapeHtml(currentStatus)}</div>
    <div><strong>updated_at</strong>: ${escapeHtml(formatDateTime(task.updated_at))}</div>
    <div><strong>next_action</strong>: ${escapeHtml(getTaskNextAction(task, statusInfo, canPerformTaskAction, canReviewTask))}</div>
  `;

  elements.submitSection.hidden = !(task.status === "TODO" && !isLoading && canPerformTaskAction);
  elements.questionSection.hidden = !(task.status === "AWAITING_A" && !isLoading && canPerformTaskAction);
  elements.resultSection.hidden = !(task.status === "DONE" && canShowResultDetails());
  elements.errorSection.hidden = !(task.status === "FAILED");
  elements.managerReviewSection.hidden = !canReviewTask;
  elements.retryButton.hidden = !canPerformTaskAction;
  elements.requestChangesButton.disabled = isTaskApproved(task);
  elements.requestChangesButton.title = isTaskApproved(task)
    ? "승인된 작업에는 보완 요청을 다시 등록할 수 없습니다."
    : "";

  elements.contentInput.value = task.content;
  elements.aiQuestion.textContent = task.ai_question || "-";
  elements.answerInput.value = task.user_answer;
  renderReviewFeedback(task);
  elements.resultAiQuestion.textContent = task.ai_question || "응답에 AI 질문이 포함되지 않았습니다.";
  elements.resultUserAnswer.textContent = task.user_answer || "응답에 user_answer가 포함되지 않았습니다.";
  elements.aiComment.textContent = task.ai_comment || "-";
  renderResultVisibility(task);
  if (isSensitiveReviewView()) {
    elements.aiComment.textContent = `${task.ai_comment || "-"}\nweighted_score: ${task.weighted_score ?? "응답 누락"}\nlocked_main_score: ${task.locked_main_score ?? "-"}\ntotal_delta_bonus: ${task.total_delta_bonus ?? 0}\nbonus_logs: ${task.bonus_logs.length}\nactivity_logs: ${task.activity_logs.length}`;
  }
  elements.errorText.textContent = state.errorMessage
    || task.error_message
    || "처리 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.";
}

function renderTaskList() {
  if (!elements.taskList) {
    return;
  }

  if (!state.tasks.length) {
    elements.taskList.innerHTML = "";
    updateListToggle(elements.taskListToggle, 0, 0, false, "개");
    return;
  }

  const visibleTasks = getVisibleItems(state.tasks, state.taskListExpanded, state.selectedTaskId, "task_id");

  elements.taskList.innerHTML = visibleTasks
    .map((task) => {
      const isSelected = task.task_id === state.selectedTaskId;
      const status = task.task_id === state.loadingTaskId && state.loadingPhase
        ? state.loadingPhase
        : task.status;
      const statusInfo = getStatusPresentation(status);
      const draft = state.drafts[task.task_id] || {};
      const hasDraft = Boolean(draft.content || draft.user_answer || task.content || task.user_answer);

      return `
        <button
          type="button"
          class="task-list-item${isSelected ? " selected" : ""}"
          data-task-id="${escapeHtml(task.task_id)}"
        >
          <span class="task-list-top">
            <strong>${escapeHtml(task.title)}</strong>
            <span class="status-badge status-${escapeHtml(status.toLowerCase())}">${escapeHtml(status)}</span>
          </span>
          <span class="task-list-meta">${escapeHtml(task.task_type)} · ${escapeHtml(formatTaskWeight(task.task_weight))}</span>
          <span class="task-list-meta">담당자: ${escapeHtml(task.client_user_name || "담당자 미지정")}</span>
          <span class="task-list-meta">보기: ${escapeHtml(getTaskViewLabel(state.taskView))}</span>
          ${canManageTask(task) ? `<span class="task-list-edit-wrap"><span class="task-list-edit-button" data-task-edit="${escapeHtml(task.task_id)}">편집</span></span>` : ""}
          <span class="task-list-action">${escapeHtml(statusInfo.actionLabel)}</span>
          <span class="task-list-note">${escapeHtml(statusInfo.note)}</span>
          <span class="task-list-note">${hasDraft ? "저장된 내용은 서버에서 다시 불러오며, 제출 전 초안만 현재 페이지에서 임시 유지됩니다." : "저장된 task를 다시 열어 이어서 진행할 수 있습니다."}</span>
        </button>
      `;
    })
    .join("");

  updateListToggle(
    elements.taskListToggle,
    state.tasks.length,
    visibleTasks.length,
    state.taskListExpanded,
    "개",
  );
}

function handleTaskListToggle() {
  state.taskListExpanded = !state.taskListExpanded;
  renderTaskList();
}

function getVisibleItems(items, expanded, selectedId, idKey) {
  if (expanded || items.length <= 3) {
    return items;
  }

  const selectedIndex = items.findIndex((item) => String(item?.[idKey] ?? "") === String(selectedId ?? ""));
  if (selectedIndex >= 3) {
    return items;
  }

  return items.slice(0, 3);
}

function shouldAutoExpandList(items, selectedId, idKey) {
  if (!items.length || items.length <= 3 || !selectedId) {
    return false;
  }

  const selectedIndex = items.findIndex((item) => String(item?.[idKey] ?? "") === String(selectedId ?? ""));
  return selectedIndex >= 3;
}

function updateListToggle(button, totalCount, visibleCount, expanded, unitLabel = "개") {
  if (!button) {
    return;
  }

  const shouldShow = totalCount > 3;
  const hiddenCount = Math.max(totalCount - visibleCount, 0);
  button.hidden = !shouldShow;
  button.textContent = expanded
    ? "접기"
    : hiddenCount > 0
      ? `나머지 ${hiddenCount}${unitLabel} 더보기`
      : "더보기";
}

function formatTaskWeight(weight) {
  switch (Number(weight)) {
    case 1:
      return "중요도 하(1)";
    case 2:
      return "중요도 중(2)";
    case 3:
      return "중요도 상(3)";
    default:
      return `중요도 ${weight}`;
  }
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatScore(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) {
    return "-";
  }
  return Number.isInteger(score) ? String(score) : String(Number(score.toFixed(2)));
}

function setCreateMessage(message) {
  elements.createMessage.textContent = message;
}

function setError(message) {
  state.errorMessage = message;
}

function clearError() {
  state.errorMessage = "";
}

function clearReviewActionMessage() {
  if (elements.reviewActionMessage) {
    elements.reviewActionMessage.textContent = "";
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
