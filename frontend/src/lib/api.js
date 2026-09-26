/**
 * api.js — Shared fetch helper for the FastAPI/LangChain backend.
 *
 * The Python backend protects /query and /documents/upload with real JWT
 * auth (OAuth2PasswordBearer). This helper transparently logs in once using
 * demo credentials and attaches the token to every request, so the rest of
 * the app can just call `apiFetch(...)` like a normal fetch — no manual
 * login screen needed for this portfolio demo.
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const DEMO_USERNAME = import.meta.env.VITE_DEMO_USERNAME || 'admin';
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || 'changeme123';

let cachedToken = null;
let tokenPromise = null;

async function fetchToken() {
  // The backend uses OAuth2PasswordRequestForm, which expects a standard
  // form-encoded body (username=...&password=...), not JSON.
  const body = new URLSearchParams();
  body.set('username', DEMO_USERNAME);
  body.set('password', DEMO_PASSWORD);

  const response = await fetch(`${API_BASE}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!response.ok) {
    throw new Error(`Login failed: HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.access_token;
}

async function getToken() {
  if (cachedToken) return cachedToken;
  if (!tokenPromise) {
    tokenPromise = fetchToken()
      .then((token) => {
        cachedToken = token;
        return token;
      })
      .finally(() => {
        tokenPromise = null;
      });
  }
  return tokenPromise;
}

/**
 * Authenticated fetch wrapper. Use exactly like `fetch(path, options)`,
 * but pass a path relative to API_BASE (e.g. "/query", "/documents/upload").
 * Automatically attaches "Authorization: Bearer <token>".
 *
 * If a request comes back 401 (e.g. token expired), it retries once after
 * forcing a fresh login.
 */
export async function apiFetch(path, options = {}, _retry = true) {
  const token = await getToken();

  const headers = { ...(options.headers || {}) };
  headers['Authorization'] = `Bearer ${token}`;
  // Don't set Content-Type for FormData — the browser needs to set its own
  // multipart boundary automatically.
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401 && _retry) {
    cachedToken = null; // force re-login
    return apiFetch(path, options, false);
  }

  return response;
}
