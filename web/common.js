const TOKEN_KEY = "eoa_token";
const ROLE_KEY = "eoa_role";
const USER_KEY = "eoa_username";
const NICK_KEY = "eoa_nickname";
const REPORT_DIR_KEY = "eoa_report_dir";

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

async function ensureUserProfile() {
  const res = await api("/api/auth/me");
  if (!res.ok) {
    return {
      username: getUsername() || getRole() || "user",
      role: getRole(),
      nickname: getNickname(),
    };
  }
  const body = await res.json();
  setSession(getToken(), body.role || getRole(), body.username || getUsername());
  return {
    username: body.username || getUsername(),
    role: body.role || getRole(),
    nickname: getNickname() || body.username || "",
  };
}

function roleLabel(role) {
  if (role === "dev") return "开发";
  if (role === "ops") return "运营";
  return role || "用户";
}
