/* localStorage 键名：登录态与用户偏好 */
const TOKEN_KEY = "eoa_token";
const ROLE_KEY = "eoa_role";
const USER_KEY = "eoa_username";
const NICK_KEY = "eoa_nickname";
const REPORT_DIR_KEY = "eoa_report_dir";

/* —— 会话读写 —— 从 localStorage 取 token / 角色 / 用户名 / 昵称 / 周报目录偏好 */
function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function getRole() {
  return localStorage.getItem(ROLE_KEY) || "";
}

function getUsername() {
  return localStorage.getItem(USER_KEY) || "";
}

function getNickname() {
  return localStorage.getItem(NICK_KEY) || getUsername() || "";
}

function getReportDirPref() {
  return localStorage.getItem(REPORT_DIR_KEY) || "reports/";
}

function setNickname(nickname) {
  localStorage.setItem(NICK_KEY, nickname || "");
}

function setReportDirPref(value) {
  localStorage.setItem(REPORT_DIR_KEY, value || "reports/");
}

function setSession(token, role, username) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
  if (username) {
    localStorage.setItem(USER_KEY, username);
    if (!localStorage.getItem(NICK_KEY)) {
      localStorage.setItem(NICK_KEY, username);
    }
  }
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_KEY);
  // keep nickname/report prefs across logout
}

/* —— API 封装 —— 带 Bearer 的 fetch；401 时清会话并跳转登录页 */
async function api(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, Object.assign({}, options, { headers }));
  if (response.status === 401) {
    clearSession();
    if (!location.pathname.endsWith("login.html")) location.href = "/login.html";
  }
  return response;
}

function requireLogin() {
  if (!getToken()) location.href = "/login.html";
}

/* —— 用户资料 —— 本地缓存与 /api/auth/me 同步；角色中文标签 */
function localProfile() {
  return {
    username: getUsername() || getRole() || "user",
    role: getRole(),
    nickname: getNickname() || getUsername() || getRole() || "user",
  };
}

async function ensureUserProfile() {
  try {
    const res = await api("/api/auth/me");
    if (!res.ok) return localProfile();
    const body = await res.json();
    setSession(getToken(), body.role || getRole(), body.username || getUsername());
    return {
      username: body.username || getUsername() || "user",
      role: body.role || getRole(),
      nickname: getNickname() || body.username || getUsername() || "user",
    };
  } catch (_) {
    return localProfile();
  }
}

function roleLabel(role) {
  if (role === "dev") return "开发";
  if (role === "ops") return "运营";
  return role || "用户";
}
