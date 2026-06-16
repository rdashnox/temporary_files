const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const TOKEN_KEYS = {
  access: 'access_token',
  refresh: 'refresh_token',
};

export const getAccessToken = () => localStorage.getItem(TOKEN_KEYS.access);
export const getRefreshToken = () => localStorage.getItem(TOKEN_KEYS.refresh);

export const setTokens = ({ access_token, refresh_token }) => {
  if (access_token) localStorage.setItem(TOKEN_KEYS.access, access_token);
  if (refresh_token) localStorage.setItem(TOKEN_KEYS.refresh, refresh_token);
};

export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
};

const safeFetch = async (url, options = {}) => {
  try {
    return await fetch(url, options);
  } catch (error) {
    throw new Error(
      `Cannot connect to the backend API through ${API_BASE_URL}. ` +
        'Start FastAPI first with python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000, then restart npm run dev.'
    );
  }
};

const parseResponse = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.detail || data.message || 'Request failed. Please try again.';
    throw new Error(message);
  }
  return data;
};

export const login = async ({ username, password }) => {
  const form = new URLSearchParams();
  form.set('username', username);
  form.set('password', password);

  const response = await safeFetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });

  const data = await parseResponse(response);
  setTokens(data);
  return data;
};

export const registerUser = async ({ username, password, confirm_password }) => {
  const response = await safeFetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, confirm_password }),
  });

  return parseResponse(response);
};

export const requestPasswordReset = async ({ username }) => {
  const response = await safeFetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username }),
  });

  return parseResponse(response);
};

export const verifyEmailToken = async (token) => {
  const response = await safeFetch(`${API_BASE_URL}/auth/verify-email?token=${encodeURIComponent(token)}`);
  return parseResponse(response);
};

export const resetPassword = async ({ token, new_password, confirm_password }) => {
  const response = await safeFetch(`${API_BASE_URL}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password, confirm_password }),
  });

  return parseResponse(response);
};

export const refreshTokens = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  const response = await safeFetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    return false;
  }

  const data = await response.json();
  setTokens(data);
  return true;
};

export const authFetch = async (path, options = {}, retried = false) => {
  const headers = new Headers(options.headers || {});
  const token = getAccessToken();

  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');

  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !retried) {
    const refreshed = await refreshTokens();
    if (refreshed) return authFetch(path, options, true);
    clearTokens();
  }

  return response;
};

export const getProducts = async () => {
  const response = await authFetch('/shop/products');
  return parseResponse(response);
};

export const checkoutCart = async (payload) => {
  const response = await authFetch('/shop/checkout', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
};

export const verifySession = async () => {
  const response = await authFetch('/data/protected');
  return parseResponse(response);
};
