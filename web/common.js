const TOKEN_KEY = "eoa_token";
const ROLE_KEY = "eoa_role";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function getRole() {
  return localStorage.getItem(ROLE_KEY) || "";
}

function setSession(token, role) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
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
