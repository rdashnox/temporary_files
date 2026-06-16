import { useEffect, useMemo, useState } from 'react';
import { verifyEmailToken } from '../api/client.js';

export default function VerifyEmailPage({ onBackToLogin }) {
  const token = useMemo(() => new URLSearchParams(window.location.search).get('token'), []);
  const [message, setMessage] = useState({ text: 'Verifying your email...', type: '' });

  useEffect(() => {
    let timeoutId;

    const verify = async () => {
      if (!token) {
        setMessage({ text: 'Verification token is missing.', type: 'error' });
        return;
      }

      try {
        const data = await verifyEmailToken(token);
        setMessage({ text: `${data.message} Redirecting to login...`, type: 'success' });
        timeoutId = window.setTimeout(onBackToLogin, 1500);
      } catch (err) {
        setMessage({ text: err.message || 'Email verification failed.', type: 'error' });
      }
    };

    verify();

    return () => {
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [onBackToLogin, token]);

  return (
    <main className="login-container auth-container legacy-auth-page">
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
