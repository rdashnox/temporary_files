const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const REQUEST_TIMEOUT_MS = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 15000);
const PRODUCT_CACHE_TTL_MS = Number(import.meta.env.VITE_PRODUCT_CACHE_TTL_MS || 60000);

const TOKEN_KEYS = {
  access: 'access_token',
  refresh: 'refresh_token',
};

export const BACKEND_OFFLINE_MESSAGE =
  `Backend API is offline. Start the backend or microservice gateway for ${API_BASE_URL}, then refresh this page.`;

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
  `${BACKEND_OFFLINE_MESSAGE} Commands: .\start-backend.ps1 or .\start-microservices-local.ps1`,
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

export const ORDER_CREATED_EVENT = 'finmark:order-created';
export const LAST_ORDER_NUMBER_KEY = 'finmark:last-order-number';

const rememberCreatedOrder = (order) => {
  if (typeof window === 'undefined' || !order) return;
  const orderNumber = order.order_id || order.order_number || '';
  if (orderNumber) {
    window.localStorage.setItem(LAST_ORDER_NUMBER_KEY, orderNumber);
  }
  window.dispatchEvent(new CustomEvent(ORDER_CREATED_EVENT, { detail: order }));
};

export const checkoutCart = async (payload) => {
  const idempotencyKey = payload.idempotency_key || createClientRequestId('checkout');
  const response = await authFetch('/orders/checkout', {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey, 'Cache-Control': 'no-cache' },
    body: JSON.stringify({ ...payload, idempotency_key: idempotencyKey }),
  });
  const result = await parseResponse(response);
  rememberCreatedOrder(result);
  return result;
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
  // Enterprise microservice mode exposes the current user through the Auth Service.
  // Older monolith builds used /database/me, so keep a fallback for compatibility.
  let response = await authFetch('/auth/me');

  if (response.status === 404) {
    response = await authFetch('/database/me');
  }

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

const ENTITY_ENDPOINTS = {
  // Enterprise microservice mode: orders are owned by the Order Service.
  // The Admin CRUD list must read from the dedicated Order Service, not the
  // legacy Auth/database routes. Compatibility fallback is still available.
  orders: '/orders',
};

const getEntityEndpoint = (entity, id = null) => {
  const base = ENTITY_ENDPOINTS[entity] || `/database/${entity}`;
  return id === null || id === undefined ? base : `${base}/${id}`;
};

const normalizeListResponse = (value) => {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  if (Array.isArray(value?.data)) return value.data;
  if (Array.isArray(value?.records)) return value.records;
  return [];
};

export const listOrdersForAdmin = async (params = {}) => {
  // Add a cache-buster so the Admin order list always re-reads the latest
  // checked-out orders from the Order Service. This prevents browser/proxy cache
  // or stale gateway responses from showing an empty list after checkout.
  const requestParams = { ...params, _ts: Date.now() };
  const query = toQueryString(requestParams);
  const endpoints = ['/orders', '/orders/', '/database/orders', '/database/orders/'];
  let lastError = null;

  for (const endpoint of endpoints) {
    try {
      const response = await authFetch(`${endpoint}${query}`, {
        headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
      });
      const data = normalizeListResponse(await parseResponse(response));
      // If the canonical Order Service returns rows, use it immediately. If it
      // returns an empty list, still try compatibility routes before giving up.
      if (data.length > 0 || endpoint.startsWith('/database')) return data;
    } catch (error) {
      lastError = error;
    }
  }

  // Last-resort fallback: if old/corrupted demo rows make the unfiltered list
  // fail, try the Order Service latest endpoint so the Admin dashboard can still
  // show recent orders while the user runs repair-order-statuses.ps1.
  if (!params.search) {
    for (const endpoint of ['/orders/latest', '/database/orders/latest']) {
      try {
        const response = await authFetch(`${endpoint}?limit=${requestParams.limit || 50}&_ts=${requestParams._ts}`, {
          headers: { 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
        });
        const data = normalizeListResponse(await parseResponse(response));
        if (data.length > 0) return data;
      } catch (error) {
        lastError = error;
      }
    }
  }

  if (lastError) throw lastError;
  return [];
};

export const listEntity = async (entity, params = {}) => {
  if (entity === 'orders') return listOrdersForAdmin(params);
  const response = await authFetch(`${getEntityEndpoint(entity)}${toQueryString(params)}`);
  return normalizeListResponse(await parseResponse(response));
};

export const createEntity = async (entity, payload) => {
  const response = await authFetch(getEntityEndpoint(entity), {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
};

export const updateEntity = async (entity, id, payload) => {
  // Orders are owned by the enterprise Order Service. Try the canonical route
  // first, then compatibility routes. This prevents Admin Edit from failing
  // when the local gateway, Nginx gateway, or a browser cache still points to
  // one of the older /database/orders paths.
  if (entity === 'orders') {
    const endpoints = [`/orders/${id}`, `/database/orders/${id}`];
    let lastError = null;
    for (const endpoint of endpoints) {
      try {
        const response = await authFetch(endpoint, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        return await parseResponse(response);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error('Unable to update order.');
  }

  const response = await authFetch(getEntityEndpoint(entity, id), {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
};

export const deleteEntity = async (entity, id) => {
  const response = await authFetch(getEntityEndpoint(entity, id), { method: 'DELETE' });
  return parseResponse(response);
};
