import { useMemo, useState } from 'react';
import { resetPassword } from '../api/client.js';
import { showApiErrorToast, showSuccessToast, showValidationToast } from '../utils/toast.js';

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

export default function ResetPasswordPage({ onBackToLogin }) {
  const token = useMemo(() => new URLSearchParams(window.location.search).get('token'), []);
  const [form, setForm] = useState({ new_password: '', confirm_password: '' });
  const [message, setMessage] = useState({ text: token ? '' : 'Password reset token is missing. Please request a new reset link.', type: token ? '' : 'error' });
  const [loading, setLoading] = useState(false);

  const updateForm = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage({ text: '', type: '' });

    if (!token) {
      const text = 'Password reset token is missing. Please request a new reset link.';
      setMessage({ text, type: 'error' });
      showValidationToast(text);
      return;
    }

    const passwordErrors = getPasswordStrengthErrors(form.new_password);
    if (passwordErrors.length > 0) {
      const text = `Password must include ${passwordErrors.join(', ')}.`;
      setMessage({ text, type: 'error' });
      showValidationToast(text);
      return;
    }

    if (form.new_password !== form.confirm_password) {
      const text = 'Passwords do not match.';
      setMessage({ text, type: 'error' });
      showValidationToast(text);
      return;
    }

    setLoading(true);

    try {
      const data = await resetPassword({
        token,
        new_password: form.new_password,
        confirm_password: form.confirm_password,
      });
      const text = `${data.message} Redirecting to login...`;
      setMessage({ text, type: 'success' });
      showSuccessToast(text);
      window.setTimeout(onBackToLogin, 1500);
    } catch (err) {
      const text = err.message || 'Password reset failed.';
      setMessage({ text, type: 'error' });
      showApiErrorToast(err, { fallback: text });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-container auth-container auth-page">
      <section className="auth-card">
        <form id="resetPasswordForm" className="login-form auth-form" onSubmit={handleSubmit}>
          <h2>Reset Password</h2>

          <div className="form-group">
            <label htmlFor="newPassword">New Password:</label>
            <input
              type="password"
              id="newPassword"
              name="new_password"
              value={form.new_password}
              onChange={updateForm}
              autoComplete="new-password"
              required
            />
            <PasswordRequirements password={form.new_password} />
          </div>

          <div className="form-group">
            <label htmlFor="confirmNewPassword">Confirm New Password:</label>
            <input
              type="password"
              id="confirmNewPassword"
              name="confirm_password"
              value={form.confirm_password}
              onChange={updateForm}
              autoComplete="new-password"
              required
            />
          </div>

          <button
            type="submit"
            data-default-label="Reset password"
            data-loading-label="Resetting..."
            className={loading ? 'is-loading' : ''}
            disabled={loading || !token}
          >
            <span className="button-spinner" aria-hidden="true" />
            <span className="button-label">{loading ? 'Resetting...' : 'Reset password'}</span>
          </button>

          <p id="resetMessage" className={`message ${message.type || ''}`} role="status" aria-live="polite">
            {message.text}
          </p>

          <p className="auth-switch-text">
            <button type="button" className="plain-link" onClick={onBackToLogin}>Back to login</button>
          </p>
        </form>
      </section>
    </main>
  );
}
