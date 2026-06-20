const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const REQUEST_TIMEOUT_MS = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 15000);
const PRODUCT_CACHE_TTL_MS = Number(import.meta.env.VITE_PRODUCT_CACHE_TTL_MS || 60000);

const TOKEN_KEYS = {
  access: 'access_token',
  refresh: 'refresh_token',
};

export const BACKEND_OFFLINE_MESSAGE =
  'Backend API is offline. Start FastAPI on http://127.0.0.1:8000, then refresh this page.';

export class BackendOfflineError extends Error {
  constructor(message = BACKEND_OFFLINE_MESSAGE) {
    super(message);
    this.name = 'BackendOfflineError';
    this.isBackendOffline = true;
  }
}

export const isBackendOfflineError = (error) => Boolean(error?.isBackendOffline);

export const AUTH_EXPIRED_EVENT = 'finmark:auth-expired';

export class AuthRequiredError extends Error {
  constructor(message = 'Your session expired. Please log in again.') {
    super(message);
    this.name = 'AuthRequiredError';
    this.isAuthRequired = true;
  }
}

export const isAuthRequiredError = (error) => Boolean(error?.isAuthRequired);

const notifyAuthExpired = () => {
  if (authExpiredAlreadyNotified) return;
  authExpiredAlreadyNotified = true;
  window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
};

export const getAccessToken = () => localStorage.getItem(TOKEN_KEYS.access);
export const getRefreshToken = () => localStorage.getItem(TOKEN_KEYS.refresh);

export const setTokens = ({ access_token, refresh_token }) => {
  authExpiredAlreadyNotified = false;
  if (access_token) localStorage.setItem(TOKEN_KEYS.access, access_token);
  if (refresh_token) localStorage.setItem(TOKEN_KEYS.refresh, refresh_token);
};

export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEYS.access);
  localStorage.removeItem(TOKEN_KEYS.refresh);
};

const makeBackendOfflineError = () => new BackendOfflineError(
  `${BACKEND_OFFLINE_MESSAGE} Command: python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`,
);

let refreshPromise = null;
let authExpiredAlreadyNotified = false;

const safeFetch = async (url, options = {}) => {
  const controller = options.signal ? null : new AbortController();
  const timeoutId = controller
    ? window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
    : null;

  try {
    return await fetch(url, {
      ...options,
      signal: options.signal || controller?.signal,
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new BackendOfflineError(`Backend API request timed out after ${REQUEST_TIMEOUT_MS}ms.`);
    }
    throw makeBackendOfflineError();
  } finally {
    if (timeoutId) window.clearTimeout(timeoutId);
  }
};

const formatApiDetail = (detail) => {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const location = Array.isArray(item.loc) ? item.loc.filter((part) => part !== 'body').join('.') : '';
        return `${location ? `${location}: ` : ''}${item.msg || 'Invalid value'}`;
      })
      .join(' ');
  }
  if (typeof detail === 'object' && detail !== null) return JSON.stringify(detail);
  return detail;
};

const parseResponse = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = formatApiDetail(data.detail) || data.message || 'Request failed. Please try again.';
    throw new Error(message);
  }
  return data;
};

export const checkBackendHealth = async () => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 2500);

  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      cache: 'no-store',
      signal: controller.signal,
    });
    return response.ok;
  } catch {
    return false;
  } finally {
    window.clearTimeout(timeoutId);
  }
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

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await safeFetch(`${API_BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
          clearTokens();
          notifyAuthExpired();
          return false;
        }

        const data = await response.json();
        setTokens(data);
        return true;
      } catch (error) {
        if (!isBackendOfflineError(error)) {
          clearTokens();
          notifyAuthExpired();
        }
        throw error;
      }
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
};

export const authFetch = async (path, options = {}, retried = false) => {
  const token = getAccessToken();
  const refreshToken = getRefreshToken();

  if (!token && !refreshToken) {
    notifyAuthExpired();
    throw new AuthRequiredError('No active session. Please log in again.');
  }

  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type') && options.body) headers.set('Content-Type', 'application/json');

  const response = await safeFetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (!retried && refreshToken) {
      const refreshed = await refreshTokens();
      if (refreshed) return authFetch(path, options, true);
    }

    clearTokens();
    notifyAuthExpired();
    throw new AuthRequiredError('Your session expired or is invalid. Please log in again.');
  }

  return response;
};

const productCache = {
  timestamp: 0,
  data: null,
  promise: null,
};

const createClientRequestId = (prefix = 'req') => {
  const randomPart = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${randomPart}`;
};

export const getProducts = async ({ forceRefresh = false } = {}) => {
  const now = Date.now();
  if (!forceRefresh && productCache.data && now - productCache.timestamp < PRODUCT_CACHE_TTL_MS) {
    return productCache.data;
  }

  if (!forceRefresh && productCache.promise) return productCache.promise;

  productCache.promise = (async () => {
    const response = await authFetch('/inventory/products');
    const data = await parseResponse(response);
    productCache.data = data;
    productCache.timestamp = Date.now();
    return data;
  })().finally(() => {
    productCache.promise = null;
  });

  return productCache.promise;
};

export const checkoutCart = async (payload) => {
  const idempotencyKey = payload.idempotency_key || createClientRequestId('checkout');
  const response = await authFetch('/orders/checkout', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    body: JSON.stringify({ ...payload, idempotency_key: idempotencyKey }),
  });
  return parseResponse(response);
};

export const getNotifications = async (params = {}) => {
  const query = toQueryString(params);
  const response = await authFetch(`/notifications${query}`);
  return parseResponse(response);
};

export const verifySession = async () => {
  const response = await authFetch('/data/protected');
  return parseResponse(response);
};

export const getCurrentDatabaseUser = async () => {
  const response = await authFetch('/database/me');
  return parseResponse(response);
};

const toQueryString = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, value);
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : '';
};

export const getDatabaseSummary = async () => {
  const response = await authFetch('/database/summary');
  return parseResponse(response);
};

export const listEntity = async (entity, params = {}) => {
  const response = await authFetch(`/database/${entity}${toQueryString(params)}`);
  return parseResponse(response);
};

export const createEntity = async (entity, payload) => {
  const response = await authFetch(`/database/${entity}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
};

export const updateEntity = async (entity, id, payload) => {
  const response = await authFetch(`/database/${entity}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
};

export const deleteEntity = async (entity, id) => {
  const response = await authFetch(`/database/${entity}/${id}`, { method: 'DELETE' });
  return parseResponse(response);
};
