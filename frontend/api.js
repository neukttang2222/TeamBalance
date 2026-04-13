const API_BASE_URL = "http://127.0.0.1:8000";
const APP_CONTEXT_STORAGE_KEY = "team-balance-app-context";
const AUTH_STORAGE_KEY = "team-balance-auth-session";

const DEFAULT_LOCAL_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_DEPLOY_API_BASE_URL = "https://teambalance.onrender.com";
const RESOLVED_API_BASE_URL = resolveApiBaseUrl();

function resolveApiBaseUrl() {
  const runtimeConfiguredUrl = window.__TEAMBALANCE_CONFIG__?.API_BASE_URL
    || window.__TEAMBALANCE_API_BASE_URL__
    || document.documentElement?.dataset?.apiBaseUrl;

  if (runtimeConfiguredUrl) {
    return String(runtimeConfiguredUrl).trim().replace(/\/+$/, "");
  }

  const hostname = window.location.hostname;
  if (hostname === "127.0.0.1" || hostname === "localhost") {
    return DEFAULT_LOCAL_API_BASE_URL;
  }

  return DEFAULT_DEPLOY_API_BASE_URL;
}

const APP_CONTEXT_OPTIONS = {
  teams: [],
  projects: [],
  users: [],
};

function getDefaultContext() {
  return {
    projectId: normalizeContextId(APP_CONTEXT_OPTIONS.projects[0]?.id),
    userId: normalizeContextId(APP_CONTEXT_OPTIONS.users[0]?.id),
  };
}

function normalizeContextId(value) {
  return value == null ? "" : String(value);
}

function normalizeContext(context = {}) {
  const projectIds = new Set(APP_CONTEXT_OPTIONS.projects.map((project) => normalizeContextId(project.id)));
  const userIds = new Set(APP_CONTEXT_OPTIONS.users.map((user) => normalizeContextId(user.id)));
  const defaults = getDefaultContext();
  const projectId = normalizeContextId(context.projectId);
  const userId = normalizeContextId(context.userId);

  return {
    projectId: projectIds.size === 0
      ? projectId || defaults.projectId
      : !projectId
        ? defaults.projectId
        : projectIds.has(projectId)
          ? projectId
          : defaults.projectId,
    userId: userIds.size === 0
      ? userId || defaults.userId
      : !userId
        ? defaults.userId
        : userIds.has(userId)
          ? userId
          : defaults.userId,
  };
}

function updateContextOptions({ teams, projects } = {}) {
  if (Array.isArray(teams)) {
    APP_CONTEXT_OPTIONS.teams = teams.map((team) => ({
      id: normalizeContextId(team.team_id ?? team.id),
      name: team.name,
      role: team.current_user_role || team.role || "",
    }));
  }

  if (Array.isArray(projects) && projects.length) {
    APP_CONTEXT_OPTIONS.projects = projects.map((project) => ({
      id: normalizeContextId(project.project_id ?? project.id),
      teamId: normalizeContextId(project.team_id ?? project.teamId),
      name: project.name,
      description: project.description || "",
      role: project.current_user_role || project.role || "",
    }));
  } else if (Array.isArray(projects)) {
    APP_CONTEXT_OPTIONS.projects = [];
  }
}

function loadAppContext() {
  try {
    const raw = window.localStorage.getItem(APP_CONTEXT_STORAGE_KEY);
    if (!raw) {
      return getDefaultContext();
    }

    return normalizeContext(JSON.parse(raw));
  } catch (error) {
    return getDefaultContext();
  }
}

function saveAppContext(context) {
  const normalized = normalizeContext(context);

  try {
    window.localStorage.setItem(APP_CONTEXT_STORAGE_KEY, JSON.stringify(normalized));
  } catch (error) {
    // 저장소 접근이 제한된 환경에서는 기본 컨텍스트를 메모리 기준으로 계속 사용합니다.
  }

  return normalized;
}

function bootstrapAppContext(context = {}) {
  const loadedContext = normalizeContext({
    ...loadAppContext(),
    ...context,
  });

  return saveAppContext(loadedContext);
}

function getProjectLabel(projectId) {
  if (!projectId) {
    return "프로젝트 미선택";
  }
  const project = APP_CONTEXT_OPTIONS.projects.find((item) => item.id === projectId);
  return project ? project.name : projectId;
}

function getProjectRole(projectId) {
  const project = APP_CONTEXT_OPTIONS.projects.find((item) => item.id === projectId);
  return project ? project.role || "" : "";
}

function getUserLabel(userId) {
  if (!userId) {
    return "사용자 미확인";
  }
  const user = APP_CONTEXT_OPTIONS.users.find((item) => item.id === userId);
  return user ? user.name : userId;
}

async function request(path, options = {}) {
  const token = loadAuthSession()?.access_token;
  const response = await fetch(`${RESOLVED_API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const message =
      (data && (data.detail || data.error_message || data.message)) ||
      `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.body = data;
    throw error;
  }

  return data;
}

function loadAuthSession() {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function saveAuthSession(session) {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  return session;
}

function clearAuthSession() {
  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}

async function login(payload) {
  const session = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return saveAuthSession(session);
}

async function signup(payload) {
  return request("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function logout() {
  try {
    await request("/auth/logout", {
      method: "POST",
    });
  } finally {
    clearAuthSession();
  }
}

async function fetchCurrentUser() {
  return request("/auth/me");
}

function getPreferredUserDisplay(user) {
  if (!user) {
    return "사용자 미확인";
  }

  const displayName = String(user.display_name || "").trim();
  const email = String(user.email || "").trim();
  const userId = String(user.user_id || user.id || "").trim();

  if (displayName && email) {
    return `${displayName} (${email})`;
  }

  return displayName || email || userId || "사용자 미확인";
}

function getSafeNextPath(fallback = "projects.html") {
  const raw = new URLSearchParams(window.location.search).get("next") || "";
  if (!raw) {
    return fallback;
  }

  const normalized = raw.replace(/^\.?\//, "");
  const allowed = new Set(["projects.html", "index.html", "dashboard.html"]);
  return allowed.has(normalized) ? normalized : fallback;
}

function buildLoginUrl(nextPath, reason = "") {
  const params = new URLSearchParams();
  if (nextPath) {
    params.set("next", nextPath.replace(/^\.?\//, ""));
  }
  if (reason) {
    params.set("reason", reason);
  }
  return `./login.html${params.toString() ? `?${params.toString()}` : ""}`;
}

function redirectToLogin(nextPath, reason = "") {
  window.location.href = buildLoginUrl(nextPath, reason);
}

function getAuthReasonMessage() {
  const reason = new URLSearchParams(window.location.search).get("reason") || "";
  if (reason === "auth_required") {
    return "로그인이 필요합니다.";
  }
  if (reason === "expired") {
    return "세션이 만료되었습니다. 다시 로그인해 주세요.";
  }
  if (reason === "logged_out") {
    return "로그아웃되었습니다.";
  }
  return "";
}

async function createTask(payload) {
  return request("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function submitTask(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}/submit`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function answerTask(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}/answer`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function retryTask(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}/retry`, {
    method: "POST",
  });
}

async function approveTask(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function requestTaskChanges(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}/request-changes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function grantDeltaBonus(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}/delta-bonuses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchContribution(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/contribution`);
}

async function fetchProjectTasks(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/tasks`);
}

async function fetchTeams() {
  return request("/teams");
}

async function createTeam(payload) {
  return request("/teams", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchTeamProjects(teamId) {
  return request(`/teams/${encodeURIComponent(teamId)}/projects`);
}

async function createProject(teamId, payload) {
  return request(`/teams/${encodeURIComponent(teamId)}/projects`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchProjectMembers(projectId) {
  return request(`/projects/${encodeURIComponent(projectId)}/members`);
}

async function addProjectMember(projectId, payload) {
  return request(`/projects/${encodeURIComponent(projectId)}/members`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchProjectTasksByView(projectId, view) {
  return request(
    `/projects/${encodeURIComponent(projectId)}/tasks?view=${encodeURIComponent(view)}`,
  );
}

async function createProjectTask(projectId, payload) {
  return request(
    `/projects/${encodeURIComponent(projectId)}/tasks`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

async function updateTask(taskId, payload) {
  return request(`/tasks/${encodeURIComponent(taskId)}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

async function deleteTask(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}`, {
    method: "DELETE",
  });
}

window.TaskApi = {
  API_BASE_URL: RESOLVED_API_BASE_URL,
  addProjectMember,
  createProject,
  createProjectTask,
  createTeam,
  createTask,
  deleteTask,
  fetchProjectMembers,
  fetchTeams,
  fetchTeamProjects,
  fetchProjectTasks,
  fetchProjectTasksByView,
  submitTask,
  answerTask,
  retryTask,
  approveTask,
  requestTaskChanges,
  grantDeltaBonus,
  updateTask,
  fetchContribution,
};

window.AuthApi = {
  login,
  signup,
  logout,
  fetchCurrentUser,
  getPreferredUserDisplay,
  getSafeNextPath,
  buildLoginUrl,
  redirectToLogin,
  getAuthReasonMessage,
  load: loadAuthSession,
  save: saveAuthSession,
  clear: clearAuthSession,
};

window.AppContext = {
  authStorageKey: AUTH_STORAGE_KEY,
  storageKey: APP_CONTEXT_STORAGE_KEY,
  options: APP_CONTEXT_OPTIONS,
  bootstrap: bootstrapAppContext,
  getDefaultContext,
  load: loadAppContext,
  save: saveAppContext,
  updateOptions: updateContextOptions,
  getProjectLabel,
  getProjectRole,
  getUserLabel,
};

