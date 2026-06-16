document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';
    const API_RESET_PASSWORD_URL = `${API_BASE_URL}/auth/reset-password`;

    const form = document.getElementById('resetPasswordForm');
    const newPassword = document.getElementById('newPassword');
    const confirmNewPassword = document.getElementById('confirmNewPassword');
    const messageElement = document.getElementById('resetMessage');
    const token = new URLSearchParams(window.location.search).get('token');

    const showMessage = (message, type = 'error') => {
        messageElement.textContent = message;
        messageElement.className = `message ${type}`;
    };

    const clearMessage = () => {
        messageElement.textContent = '';
        messageElement.className = 'message';
    };

    const getPasswordStrengthStatus = (password) => ({
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        number: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
    });

    const updatePasswordRequirementUI = () => {
        const status = getPasswordStrengthStatus(newPassword.value);
        document.querySelectorAll('#passwordRequirements [data-rule]').forEach((item) => {
            const rule = item.dataset.rule;
            item.classList.toggle('valid', Boolean(status[rule]));
        });
    };

    const getPasswordStrengthErrors = (password) => {
        const status = getPasswordStrengthStatus(password);
        const errors = [];

        if (!status.length) errors.push('at least 8 characters');
        if (!status.lowercase) errors.push('one lowercase letter');
        if (!status.uppercase) errors.push('one uppercase letter');
        if (!status.number) errors.push('one number');
        if (!status.special) errors.push('one special character');

        return errors;
    };

    const setButtonLoading = (button, isLoading) => {
        const label = button.querySelector('.button-label');
        const defaultLabel = button.dataset.defaultLabel || button.textContent;
        const loadingLabel = button.dataset.loadingLabel || 'Loading...';

        button.disabled = isLoading;
        button.classList.toggle('is-loading', isLoading);
        if (label) {
            label.textContent = isLoading ? loadingLabel : defaultLabel;
        }
    };

    if (!token) {
        showMessage('Password reset token is missing. Please request a new reset link.');
        form.querySelector('button[type="submit"]').disabled = true;
    }

    newPassword.addEventListener('input', updatePasswordRequirementUI);

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearMessage();

        const password = newPassword.value;
        const confirmPassword = confirmNewPassword.value;
        const submitButton = form.querySelector('button[type="submit"]');
        const passwordErrors = getPasswordStrengthErrors(password);

        if (passwordErrors.length > 0) {
            showMessage(`Password must include ${passwordErrors.join(', ')}.`);
            return;
        }

        if (password !== confirmPassword) {
            showMessage('Passwords do not match.');
            return;
        }

        setButtonLoading(submitButton, true);

        try {
            const response = await fetch(API_RESET_PASSWORD_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token,
                    new_password: password,
                    confirm_password: confirmPassword,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(data.detail || 'Password reset failed.');
                return;
            }

            showMessage(`${data.message} Redirecting to login...`, 'success');
            setTimeout(() => window.location.replace('index.html'), 1500);
        } catch (error) {
            showMessage('Unable to connect to the backend. Please make sure the API server is running.');
            console.error('Reset password error:', error);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });

    updatePasswordRequirementUI();
});
