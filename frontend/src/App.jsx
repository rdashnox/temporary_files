import { useCallback, useEffect, useMemo, useState } from 'react';
import { AUTH_EXPIRED_EVENT, clearTokens, getAccessToken, getRefreshToken, getCurrentDatabaseUser, login, verifySession } from './api/client.js';
import DashboardRouter from './pages/DashboardRouter.jsx';
import LoginPage from './pages/LoginPage.jsx';
import ResetPasswordPage from './pages/ResetPasswordPage.jsx';
import VerifyEmailPage from './pages/VerifyEmailPage.jsx';

const getAuthRoute = () => {
  const path = window.location.pathname.toLowerCase();
  if (path.endsWith('/verify-email.html') || path.endsWith('/verify-email')) return 'verify-email';
  if (path.endsWith('/reset-password.html') || path.endsWith('/reset-password')) return 'reset-password';
  return 'login';
};

export default function App() {
  const [session, setSession] = useState({ status: 'checking', user: null });
  const [authRoute, setAuthRoute] = useState(getAuthRoute);

  const isLoggedIn = useMemo(
    () => session.status === 'authenticated' && Boolean(session.user),
    [session],
  );

  const goToLogin = useCallback(() => {
    window.history.replaceState({}, '', '/');
    setAuthRoute('login');
    setSession((current) => (current.status === 'authenticated' ? current : { status: 'guest', user: null }));
  }, []);


  useEffect(() => {
    const handleAuthExpired = () => {
      clearTokens();
      setSession({ status: 'guest', user: null });
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
  }, []);

  useEffect(() => {
    const handleNavigation = () => setAuthRoute(getAuthRoute());
    window.addEventListener('popstate', handleNavigation);
    return () => window.removeEventListener('popstate', handleNavigation);
  }, []);

  useEffect(() => {
    const bootstrapSession = async () => {
      if (authRoute !== 'login') {
        setSession({ status: 'guest', user: null });
        return;
      }

      if (!getAccessToken() && !getRefreshToken()) {
        setSession({ status: 'guest', user: null });
        return;
      }

      try {
        await verifySession();
        const user = await getCurrentDatabaseUser();
        setSession({ status: 'authenticated', user });
      } catch {
        clearTokens();
        setSession({ status: 'guest', user: null });
      }
    };

    bootstrapSession();
  }, [authRoute]);

  const handleLogin = async (credentials) => {
    const tokenData = await login(credentials);
    await verifySession();
    const user = await getCurrentDatabaseUser();
    setSession({ status: 'authenticated', user });
    return tokenData;
  };

  const handleLogout = () => {
    clearTokens();
    setSession({ status: 'guest', user: null });
  };

  if (authRoute === 'verify-email') {
    return <VerifyEmailPage onBackToLogin={goToLogin} />;
  }

  if (authRoute === 'reset-password') {
    return <ResetPasswordPage onBackToLogin={goToLogin} />;
  }

  if (session.status === 'checking') {
    return (
      <main className="screen-center">
        <div className="loading-card glass-card">
          <div className="spinner" />
          <p>Preparing your FinMark dashboard...</p>
        </div>
      </main>
    );
  }

  return isLoggedIn ? (
    <DashboardRouter user={session.user} onLogout={handleLogout} />
  ) : (
    <LoginPage onLogin={handleLogin} />
  );
}
