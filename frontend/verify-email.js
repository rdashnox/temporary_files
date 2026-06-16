document.addEventListener('DOMContentLoaded', async () => {
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';
    const messageElement = document.getElementById('verifyMessage');
    const token = new URLSearchParams(window.location.search).get('token');

    const showMessage = (message, type = 'error') => {
        messageElement.textContent = message;
        messageElement.className = `message ${type}`;
    };

    if (!token) {
        showMessage('Verification token is missing.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-email?token=${encodeURIComponent(token)}`);
        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || 'Email verification failed.');
            return;
        }

        showMessage(`${data.message} Redirecting to login...`, 'success');
        setTimeout(() => window.location.replace('index.html'), 1500);
    } catch (error) {
        showMessage('Unable to connect to the backend. Please make sure the API server is running.');
        console.error('Email verification error:', error);
    }
});
