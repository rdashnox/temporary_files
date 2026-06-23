import { useMemo, useState } from 'react';
import { registerUser, requestPasswordReset } from '../api/client.js';
import { showApiErrorToast, showErrorToast, showSuccessToast, showValidationToast } from '../utils/toast.js';

const INITIAL_LOGIN = {
  username: '',
  password: '',
};

const INITIAL_REGISTER = {
  username: '',
  password: '',
  confirm_password: '',
};

const INITIAL_FORGOT = {
  username: '',
};

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

const isValidEmail = (email) => /\S+@\S+\.\S+/.test(email);

function Message({ state }) {
  if (!state?.text) return <p className="message" role="status" aria-live="polite" />;
  return <p className={`message ${state.type || 'error'}`} role="status" aria-live="polite">{state.text}</p>;
}

function SubmitButton({ loading, defaultLabel, loadingLabel }) {
  return (
    <button
      type="submit"
      data-default-label={defaultLabel}
      data-loading-label={loadingLabel}
      className={loading ? 'is-loading' : ''}
      disabled={loading}
    >
      <span className="button-spinner" aria-hidden="true" />
      <span className="button-label">{loading ? loadingLabel : defaultLabel}</span>
    </button>
  );
}

function PasswordRequirements({ password }) {
  const status = getPasswordStrengthStatus(password);
  return (
    <ul id="passwordRequirements" className="password-requirements" aria-live="polite">
      <li data-rule="length" className={status.length ? 'valid' : ''}>At least 8 characters</li>
      <li data-rule="lowercase" className={status.lowercase ? 'valid' : ''}>One lowercase letter</li>
      <li data-rule="uppercase" className={status.uppercase ? 'valid' : ''}>One uppercase letter</li>
      <li data-rule="number" className={status.number ? 'valid' : ''}>One number</li>
      <li data-rule="special" className={status.special ? 'valid' : ''}>One special character</li>
    </ul>
  );
}

export default function LoginPage({ onLogin }) {
  const [activeForm, setActiveForm] = useState('login');
  const [loginForm, setLoginForm] = useState(INITIAL_LOGIN);
  const [registerForm, setRegisterForm] = useState(INITIAL_REGISTER);
  const [forgotForm, setForgotForm] = useState(INITIAL_FORGOT);
  const [messages, setMessages] = useState({});
  const [loading, setLoading] = useState({});
  const [verificationLink, setVerificationLink] = useState('');
  const [resetLink, setResetLink] = useState('');

  const registerPasswordErrors = useMemo(
    () => getPasswordStrengthErrors(registerForm.password),
    [registerForm.password],
  );

  const setMessage = (key, text, type = 'error', { silent = false } = {}) => {
    setMessages((current) => ({ ...current, [key]: { text, type } }));
    if (!silent && text) {
      if (type === 'success') showSuccessToast(text);
      else if (type === 'warning') showValidationToast(text);
      else showErrorToast(text);
    }
  };

  const clearMessage = (key) => {
    setMessages((current) => ({ ...current, [key]: { text: '', type: '' } }));
  };

  const showLoginView = () => {
    setActiveForm('login');
    clearMessage('register');
    clearMessage('forgot');
    setVerificationLink('');
    setResetLink('');
  };

  const showRegisterView = () => {
    setActiveForm('register');
    clearMessage('login');
    clearMessage('forgot');
    setVerificationLink('');
    setResetLink('');
    setRegisterForm((current) => ({
      ...current,
      username: current.username || loginForm.username.trim(),
    }));
  };

  const showForgotPasswordView = () => {
    setActiveForm('forgot');
    clearMessage('login');
    clearMessage('register');
    setVerificationLink('');
    setResetLink('');
    setForgotForm((current) => ({
      ...current,
      username: current.username || loginForm.username.trim(),
    }));
  };

  const updateLoginForm = (event) => {
    const { name, value } = event.target;
    setLoginForm((current) => ({ ...current, [name]: value }));
  };

  const updateRegisterForm = (event) => {
    const { name, value } = event.target;
    setRegisterForm((current) => ({ ...current, [name]: value }));
  };

  const updateForgotForm = (event) => {
    const { name, value } = event.target;
    setForgotForm((current) => ({ ...current, [name]: value }));
  };

  const validateEmail = (username, messageKey) => {
    if (!username) {
      setMessage(messageKey, 'Email cannot be empty.');
      return false;
    }

    if (!isValidEmail(username)) {
      setMessage(messageKey, 'Please enter a valid email address.');
      return false;
    }

    return true;
  };

  const handleLoginSubmit = async (event) => {
    event.preventDefault();
    const username = loginForm.username.trim();
    const password = loginForm.password;

    clearMessage('login');

    if (!validateEmail(username, 'login')) return;
    if (!password.trim()) {
      setMessage('login', 'Password cannot be empty.');
      return;
    }

    setLoading((current) => ({ ...current, login: true }));

    try {
      await onLogin({ username, password });
      showSuccessToast('Login successful. Welcome back.');
    } catch (err) {
      setMessage('login', `Login failed: ${err.message || 'Invalid credentials.'}`, 'error', { silent: true });
      showApiErrorToast(err, { fallback: 'Login failed. Please check your credentials.' });
    } finally {
      setLoading((current) => ({ ...current, login: false }));
    }
  };

  const handleRegisterSubmit = async (event) => {
    event.preventDefault();
    const username = registerForm.username.trim();
    const password = registerForm.password;
    const confirmPassword = registerForm.confirm_password;

    clearMessage('register');
    setVerificationLink('');

    if (!validateEmail(username, 'register')) return;
    if (registerPasswordErrors.length > 0) {
      setMessage('register', `Password must include ${registerPasswordErrors.join(', ')}.`);
      return;
    }
    if (password !== confirmPassword) {
      setMessage('register', 'Passwords do not match.');
      return;
    }

    setLoading((current) => ({ ...current, register: true }));

    try {
      const data = await registerUser({ username, password, confirm_password: confirmPassword });
      const nextVerificationLink = data.verification_link || `/verify-email.html?token=${encodeURIComponent(data.verification_token)}`;
      setRegisterForm(INITIAL_REGISTER);
      setLoginForm({ username, password: '' });
      setVerificationLink(nextVerificationLink);
      setMessage('register', 'Account created. Please verify your email before logging in.', 'success');
    } catch (err) {
      setMessage('register', `Registration failed: ${err.message || 'Unable to create account.'}`, 'error', { silent: true });
      showApiErrorToast(err, { fallback: 'Registration failed. Please check the form.' });
    } finally {
      setLoading((current) => ({ ...current, register: false }));
    }
  };

  const handleForgotSubmit = async (event) => {
    event.preventDefault();
    const username = forgotForm.username.trim();

    clearMessage('forgot');
    setResetLink('');

    if (!validateEmail(username, 'forgot')) return;

    setLoading((current) => ({ ...current, forgot: true }));

    try {
      const data = await requestPasswordReset({ username });
      setMessage('forgot', data.message || 'If the account exists, a password reset link has been generated.', 'success');
      if (data.reset_link) setResetLink(data.reset_link);
    } catch (err) {
      setMessage('forgot', `Request failed: ${err.message || 'Unable to generate reset link.'}`, 'error', { silent: true });
      showApiErrorToast(err, { fallback: 'Unable to generate reset link.' });
    } finally {
      setLoading((current) => ({ ...current, forgot: false }));
    }
  };

  return (
    <main className="login-container auth-container auth-page">
      <section className="auth-card">
        <form
          id="loginForm"
          className={`login-form auth-form ${activeForm === 'login' ? '' : 'hidden'}`}
          aria-hidden={activeForm !== 'login'}
          onSubmit={handleLoginSubmit}
        >
          <h2>FinMark Login</h2>

          <div className="form-group">
            <label htmlFor="loginUsername">Email:</label>
            <input
              type="email"
              id="loginUsername"
              name="username"
              value={loginForm.username}
              onChange={updateLoginForm}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="loginPassword">Password:</label>
            <input
              type="password"
              id="loginPassword"
              name="password"
              value={loginForm.password}
              onChange={updateLoginForm}
              autoComplete="current-password"
              required
            />
          </div>

          <SubmitButton loading={loading.login} defaultLabel="Login" loadingLabel="Logging in..." />
          <Message state={messages.login} />

          <p className="auth-switch-text">
            <button type="button" id="showForgotPasswordButton" className="link-button" onClick={showForgotPasswordView}>Forgot password?</button>
          </p>

          <p className="auth-switch-text">
            Don&apos;t have an account?{' '}
            <button type="button" id="showRegisterButton" className="link-button" onClick={showRegisterView}>Create account</button>
          </p>
        </form>

        <form
          id="registerForm"
          className={`login-form auth-form ${activeForm === 'register' ? '' : 'hidden'}`}
          aria-hidden={activeForm !== 'register'}
          onSubmit={handleRegisterSubmit}
        >
          <h2>Create Account</h2>

          <div className="form-group">
            <label htmlFor="registerUsername">Email:</label>
            <input
              type="email"
              id="registerUsername"
              name="username"
              value={registerForm.username}
              onChange={updateRegisterForm}
              autoComplete="email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="registerPassword">Password:</label>
            <input
              type="password"
              id="registerPassword"
              name="password"
              value={registerForm.password}
              onChange={updateRegisterForm}
              autoComplete="new-password"
              required
            />
            <PasswordRequirements password={registerForm.password} />
          </div>

          <div className="form-group">
            <label htmlFor="registerConfirmPassword">Confirm Password:</label>
            <input
              type="password"
              id="registerConfirmPassword"
              name="confirm_password"
              value={registerForm.confirm_password}
              onChange={updateRegisterForm}
              autoComplete="new-password"
              required
            />
          </div>

          <SubmitButton loading={loading.register} defaultLabel="Register" loadingLabel="Registering..." />
          <Message state={messages.register} />

          {verificationLink && (
            <div id="verificationDemoBox" className="demo-box">
              <strong>Demo verification link:</strong>
              <p>In production, this link should be sent by email.</p>
              <a id="verificationDemoLink" href={verificationLink}>Verify email now</a>
            </div>
          )}

          <p className="auth-switch-text">
            Already have an account?{' '}
            <button type="button" id="showLoginButton" className="link-button" onClick={showLoginView}>Back to login</button>
          </p>
        </form>

        <form
          id="forgotPasswordForm"
          className={`login-form auth-form ${activeForm === 'forgot' ? '' : 'hidden'}`}
          aria-hidden={activeForm !== 'forgot'}
          onSubmit={handleForgotSubmit}
        >
          <h2>Forgot Password</h2>
          <p className="form-hint">Enter your email to generate a reset link.</p>

          <div className="form-group">
            <label htmlFor="forgotUsername">Email:</label>
            <input
              type="email"
              id="forgotUsername"
              name="username"
              value={forgotForm.username}
              onChange={updateForgotForm}
              autoComplete="email"
              required
            />
          </div>

          <SubmitButton loading={loading.forgot} defaultLabel="Send reset link" loadingLabel="Sending..." />
          <Message state={messages.forgot} />

          {resetLink && (
            <div id="resetDemoBox" className="demo-box">
              <strong>Demo reset link:</strong>
              <p>In production, this link should be sent by email.</p>
              <a id="resetDemoLink" href={resetLink}>Reset password now</a>
            </div>
          )}

          <p className="auth-switch-text">
            <button type="button" id="backToLoginFromForgotButton" className="link-button" onClick={showLoginView}>Back to login</button>
          </p>
        </form>
      </section>
    </main>
  );
}
