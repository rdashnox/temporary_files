(function () {
    const TOKEN_STORAGE_KEYS = {
        accessToken: 'access_token',
        refreshToken: 'refresh_token',
    };

    const getApiBaseUrl = () => window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';

    const getAccessToken = () => localStorage.getItem(TOKEN_STORAGE_KEYS.accessToken);
    const getRefreshToken = () => localStorage.getItem(TOKEN_STORAGE_KEYS.refreshToken);

    const setTokens = ({ access_token, refresh_token }) => {
        if (access_token) {
            localStorage.setItem(TOKEN_STORAGE_KEYS.accessToken, access_token);
        }
        if (refresh_token) {
            localStorage.setItem(TOKEN_STORAGE_KEYS.refreshToken, refresh_token);
        }
    };

    const clearTokens = () => {
        localStorage.removeItem(TOKEN_STORAGE_KEYS.accessToken);
        localStorage.removeItem(TOKEN_STORAGE_KEYS.refreshToken);
    };

    const logout = () => {
        clearTokens();
        window.location.replace('index.html');
    };

    const refreshTokens = async () => {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
            return false;
        }

        const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
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

    const authFetch = async (url, options = {}, hasRetried = false) => {
        const token = getAccessToken();
        const headers = new Headers(options.headers || {});

        if (token) {
            headers.set('Authorization', `Bearer ${token}`);
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (response.status !== 401 || hasRetried) {
            return response;
        }

        const didRefresh = await refreshTokens();
        if (!didRefresh) {
            return response;
        }

        return authFetch(url, options, true);
    };

    const requireAuth = async ({ onSuccess, onFailure } = {}) => {
        if (!getAccessToken() && !getRefreshToken()) {
            logout();
            return;
        }

        const response = await authFetch(`${getApiBaseUrl()}/data/protected`);

        if (!response.ok) {
            clearTokens();
            if (onFailure) {
                onFailure();
            } else {
                window.location.replace('index.html');
            }
            return;
        }

        const data = await response.json();
        if (onSuccess) {
            onSuccess(data);
        }
    };

    window.Auth = {
        TOKEN_STORAGE_KEYS,
        getAccessToken,
        getRefreshToken,
        setTokens,
        clearTokens,
        logout,
        refreshTokens,
        authFetch,
        requireAuth,
    };
}());
