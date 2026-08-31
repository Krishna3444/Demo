// client.js — shared HTTP client + token management.
//
// The JWT access token is kept in localStorage (same architecture as the
// original app). Every request carries `Authorization: Bearer <token>`.
// On 401 the auth state is cleared and an `dhaniti:unauthorized` event is
// dispatched so the AuthProvider can redirect to /login exactly once.

const TOKEN_KEY = "dhaniti_token";
const USER_KEY = "dhaniti_user";

export class ApiError extends Error {
  constructor(message, status, details = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser() {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// Use relative URLs so it works in dev (Vite proxy) and prod (same origin).
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(path, { ...options, headers });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }

  if (res.status === 401) {
    const wasLoggedIn = Boolean(getToken());
    clearAuth();
    if (wasLoggedIn && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("dhaniti:unauthorized"));
    }
    let msg = "Your session has expired. Please sign in again.";
    try {
      const body = await res.json();
      if (body && body.error) msg = body.error;
    } catch {
      /* ignore */
    }
    throw new ApiError(msg, 401);
  }

  if (res.status === 204) return null;

  let body = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON response */
  }

  if (!res.ok) {
    const message =
      (body && (body.error || body.detail)) ||
      (res.status === 429 ? "Too many attempts. Please wait a moment and try again." : null) ||
      `Request failed (HTTP ${res.status})`;
    const details = (body && body.details) || [];
    throw new ApiError(message, res.status, Array.isArray(details) ? details : []);
  }
  return body;
}

export { apiFetch };
