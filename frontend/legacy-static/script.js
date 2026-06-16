document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1';
    const API_LOGIN_URL = `${API_BASE_URL}/auth/token`;
    const API_REGISTER_URL = `${API_BASE_URL}/auth/register`;
    const API_FORGOT_PASSWORD_URL = `${API_BASE_URL}/auth/forgot-password`;

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const forgotPasswordForm = document.getElementById('forgotPasswordForm');

    const loginMessageElement = document.getElementById('loginMessage');
    const registerMessageElement = document.getElementById('registerMessage');
    const forgotMessageElement = document.getElementById('forgotMessage');

    const showRegisterButton = document.getElementById('showRegisterButton');
    const showLoginButton = document.getElementById('showLoginButton');
    const showForgotPasswordButton = document.getElementById('showForgotPasswordButton');
    const backToLoginFromForgotButton = document.getElementById('backToLoginFromForgotButton');

    const registerPassword = document.getElementById('registerPassword');
    const registerConfirmPassword = document.getElementById('registerConfirmPassword');
    const verificationDemoBox = document.getElementById('verificationDemoBox');
    const verificationDemoLink = document.getElementById('verificationDemoLink');
    const resetDemoBox = document.getElementById('resetDemoBox');
    const resetDemoLink = document.getElementById('resetDemoLink');

    const showMessage = (element, message, type = 'error') => {
        element.textContent = message;
        element.className = `message ${type}`;
    };

    const clearMessage = (element) => {
        element.textContent = '';
        element.className = 'message';
    };

    const setFormVisibility = (form, isVisible) => {
        form.classList.toggle('hidden', !isVisible);
        form.setAttribute('aria-hidden', String(!isVisible));
    };

    const hideDemoBoxes = () => {
        verificationDemoBox.classList.add('hidden');
        resetDemoBox.classList.add('hidden');
    };

    const showOnlyForm = (visibleForm) => {
        [loginForm, registerForm, forgotPasswordForm].forEach((form) => {
            setFormVisibility(form, form === visibleForm);
        });
    };

    const showLoginView = () => {
        showOnlyForm(loginForm);
        clearMessage(registerMessageElement);
        clearMessage(forgotMessageElement);
        hideDemoBoxes();
        document.getElementById('loginUsername').focus();
    };

    const showRegisterView = () => {
        showOnlyForm(registerForm);
        clearMessage(loginMessageElement);
        clearMessage(forgotMessageElement);
        hideDemoBoxes();

        const loginUsername = document.getElementById('loginUsername').value.trim();
        const registerUsername = document.getElementById('registerUsername');

        if (loginUsername && !registerUsername.value) {
            registerUsername.value = loginUsername;
        }

        registerUsername.focus();
    };

    const showForgotPasswordView = () => {
        showOnlyForm(forgotPasswordForm);
        clearMessage(loginMessageElement);
        clearMessage(registerMessageElement);
        hideDemoBoxes();

        const loginUsername = document.getElementById('loginUsername').value.trim();
        const forgotUsername = document.getElementById('forgotUsername');

        if (loginUsername && !forgotUsername.value) {
            forgotUsername.value = loginUsername;
        }

        forgotUsername.focus();
    };

    const isValidEmail = (email) => /\S+@\S+\.\S+/.test(email);

    const getPasswordStrengthStatus = (password) => ({
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        number: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
    });

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

    const updatePasswordRequirementUI = () => {
        const status = getPasswordStrengthStatus(registerPassword.value);
        document.querySelectorAll('#passwordRequirements [data-rule]').forEach((item) => {
            const rule = item.dataset.rule;
            item.classList.toggle('valid', Boolean(status[rule]));
        });
    };

    const validateEmail = (username, messageElement) => {
        if (!username) {
            showMessage(messageElement, 'Email cannot be empty.');
            return false;
        }

        if (!isValidEmail(username)) {
            showMessage(messageElement, 'Please enter a valid email address.');
            return false;
        }

        return true;
    };

    const validateLoginCredentials = (username, password, messageElement) => {
        if (!validateEmail(username, messageElement)) {
            return false;
        }

        if (!password.trim()) {
            showMessage(messageElement, 'Password cannot be empty.');
            return false;
        }

        return true;
    };

    const validateRegistrationCredentials = (username, password, confirmPassword, messageElement) => {
        if (!validateEmail(username, messageElement)) {
            return false;
        }

        const passwordErrors = getPasswordStrengthErrors(password);
        if (passwordErrors.length > 0) {
            showMessage(messageElement, `Password must include ${passwordErrors.join(', ')}.`);
            return false;
        }

        if (password !== confirmPassword) {
            showMessage(messageElement, 'Passwords do not match.');
            return false;
        }

        return true;
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

    showRegisterButton.addEventListener('click', showRegisterView);
    showLoginButton.addEventListener('click', showLoginView);
    showForgotPasswordButton.addEventListener('click', showForgotPasswordView);
    backToLoginFromForgotButton.addEventListener('click', showLoginView);
    registerPassword.addEventListener('input', updatePasswordRequirementUI);
    registerConfirmPassword.addEventListener('input', () => clearMessage(registerMessageElement));

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const submitButton = loginForm.querySelector('button[type="submit"]');

        clearMessage(loginMessageElement);

        if (!validateLoginCredentials(username, password, loginMessageElement)) {
            return;
        }

        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        setButtonLoading(submitButton, true);

        try {
            const response = await fetch(API_LOGIN_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(loginMessageElement, `Login failed: ${data.detail || 'Invalid credentials.'}`);
                return;
            }

            if (!data.access_token || !data.refresh_token) {
                showMessage(loginMessageElement, 'Login failed: backend did not return complete tokens.');
                return;
            }

            window.Auth.setTokens(data);
            window.location.assign('dashboard.html');
        } catch (error) {
            showMessage(loginMessageElement, 'Unable to connect to the backend. Please make sure the API server is running.');
            console.error('Login error:', error);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });

    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = document.getElementById('registerUsername').value.trim();
        const password = registerPassword.value;
        const confirmPassword = registerConfirmPassword.value;
        const submitButton = registerForm.querySelector('button[type="submit"]');

        clearMessage(registerMessageElement);
        hideDemoBoxes();

        if (!validateRegistrationCredentials(username, password, confirmPassword, registerMessageElement)) {
            return;
        }

        setButtonLoading(submitButton, true);

        try {
            const response = await fetch(API_REGISTER_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    confirm_password: confirmPassword,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(registerMessageElement, `Registration failed: ${data.detail || 'Unable to create account.'}`);
                return;
            }

            registerForm.reset();
            updatePasswordRequirementUI();
            document.getElementById('loginUsername').value = username;
            document.getElementById('loginPassword').value = '';
            verificationDemoLink.href = data.verification_link || `verify-email.html?token=${encodeURIComponent(data.verification_token)}`;
            verificationDemoBox.classList.remove('hidden');
            showMessage(registerMessageElement, 'Account created. Please verify your email before logging in.', 'success');
        } catch (error) {
            showMessage(registerMessageElement, 'Unable to connect to the backend. Please make sure the API server is running.');
            console.error('Registration error:', error);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });

    forgotPasswordForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const username = document.getElementById('forgotUsername').value.trim();
        const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');

        clearMessage(forgotMessageElement);
        hideDemoBoxes();

        if (!validateEmail(username, forgotMessageElement)) {
            return;
        }

        setButtonLoading(submitButton, true);

        try {
            const response = await fetch(API_FORGOT_PASSWORD_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username }),
            });

            const data = await response.json();

            if (!response.ok) {
                showMessage(forgotMessageElement, `Request failed: ${data.detail || 'Unable to generate reset link.'}`);
                return;
            }

            showMessage(forgotMessageElement, data.message, 'success');

            if (data.reset_link) {
                resetDemoLink.href = data.reset_link;
                resetDemoBox.classList.remove('hidden');
            }
        } catch (error) {
            showMessage(forgotMessageElement, 'Unable to connect to the backend. Please make sure the API server is running.');
            console.error('Forgot password error:', error);
        } finally {
            setButtonLoading(submitButton, false);
        }
    });

    updatePasswordRequirementUI();
});
