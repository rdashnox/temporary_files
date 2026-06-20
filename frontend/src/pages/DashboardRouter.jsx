import { useCallback, useEffect, useMemo, useState } from 'react';
import AdminDashboard from './AdminDashboard.jsx';
import CartDashboard from './CartDashboard.jsx';
import { canOpenAdminDashboard, canOpenProductDashboard, normalizeUser } from '../utils/access.js';

const getRequestedDashboard = () => {
  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();

  if (path.includes('/admin') || hash === '#admin') return 'admin';
  if (path.includes('/products') || path.includes('/product') || path.includes('/dashboard') || hash === '#products') return 'products';
  return 'products';
};

export default function DashboardRouter({ user: rawUser, onLogout }) {
  const user = useMemo(() => normalizeUser(rawUser), [rawUser]);
  const canViewProducts = canOpenProductDashboard(user);
  const canViewAdmin = canOpenAdminDashboard(user);

  const resolveDashboard = useCallback(() => {
    const requested = getRequestedDashboard();
    if (requested === 'admin' && canViewAdmin) return 'admin';
    if (canViewProducts) return 'products';
    return 'products';
  }, [canViewAdmin, canViewProducts]);

  const [activeDashboard, setActiveDashboard] = useState(resolveDashboard);
  const [requestedAdminEntity, setRequestedAdminEntity] = useState(null);

  useEffect(() => {
    const handleNavigation = () => setActiveDashboard(resolveDashboard());
    window.addEventListener('popstate', handleNavigation);
    return () => window.removeEventListener('popstate', handleNavigation);
  }, [resolveDashboard]);

  useEffect(() => {
    setActiveDashboard(resolveDashboard());
  }, [resolveDashboard]);

  const openDashboard = useCallback((dashboard, options = {}) => {
    if (dashboard === 'admin' && !canViewAdmin) return;
    if (dashboard === 'products' && !canViewProducts) return;

    if (dashboard === 'admin') {
      setRequestedAdminEntity(options.entity || null);
    }

    const targetPath = dashboard === 'admin' ? '/admin' : '/products';
    window.history.pushState({}, '', targetPath);
    setActiveDashboard(dashboard);
  }, [canViewAdmin, canViewProducts]);

  if (activeDashboard === 'admin' && canViewAdmin) {
    return (
      <AdminDashboard
        user={user}
        onLogout={onLogout}
        onOpenProducts={() => openDashboard('products')}
        canOpenProducts={canViewProducts}
        initialEntity={requestedAdminEntity}
      />
    );
  }

  return (
    <CartDashboard
      user={user}
      onLogout={onLogout}
      onOpenAdmin={(entity) => openDashboard('admin', { entity })}
      canOpenAdmin={canViewAdmin}
    />
  );
}
