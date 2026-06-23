import { useEffect, useMemo, useState } from 'react';
import { verifyEmailToken } from '../api/client.js';
import { showApiErrorToast, showSuccessToast, showValidationToast } from '../utils/toast.js';

export default function VerifyEmailPage({ onBackToLogin }) {
  const token = useMemo(() => new URLSearchParams(window.location.search).get('token'), []);
  const [message, setMessage] = useState({ text: 'Verifying your email...', type: '' });

  useEffect(() => {
    let timeoutId;

    const verify = async () => {
      if (!token) {
        const text = 'Verification token is missing.';
        setMessage({ text, type: 'error' });
        showValidationToast(text);
        return;
      }

      try {
        const data = await verifyEmailToken(token);
        const text = `${data.message} Redirecting to login...`;
        setMessage({ text, type: 'success' });
        showSuccessToast(text);
        timeoutId = window.setTimeout(onBackToLogin, 1500);
      } catch (err) {
        const text = err.message || 'Email verification failed.';
        setMessage({ text, type: 'error' });
        showApiErrorToast(err, { fallback: text });
      }
    };

    verify();

    return () => {
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [onBackToLogin, token]);

  return (
    <main className="login-container auth-container auth-page">
      <section className="auth-card">
        <h2>Verify Email</h2>
        <p id="verifyMessage" className={`message ${message.type || ''}`} role="status" aria-live="polite">
          {message.text}
        </p>
        <p className="auth-switch-text">
          <button type="button" className="plain-link" onClick={onBackToLogin}>Back to login</button>
        </p>
      </section>
    </main>
  );
}
