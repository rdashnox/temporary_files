export const PRODUCT_DASHBOARD_ROLES = ['admin', 'staff', 'viewer', 'user', 'customer'];
export const ADMIN_DASHBOARD_ROLES = ['admin', 'manager'];
export const PRODUCT_ONLY_ROLES = ['customer'];

export const normalizeUser = (user) => {
  if (!user) return { username: 'User', email: '', roles: [], permissions: [] };
  if (typeof user === 'string') return { username: user, email: user, roles: [], permissions: [] };
  return {
    ...user,
    username: user.username || user.email || user.full_name || 'User',
    roles: Array.isArray(user.roles) ? user.roles : [],
    permissions: Array.isArray(user.permissions) ? user.permissions : [],
  };
};

export const getDisplayName = (user) => {
  const normalized = normalizeUser(user);
  return normalized.full_name || normalized.username || normalized.email || 'User';
};

export const getRoleNames = (user) => {
  const normalized = normalizeUser(user);
  return normalized.roles
    .map((role) => {
      if (typeof role === 'string') return role;
      return role?.name || role?.code || '';
    })
    .filter(Boolean)
    .map((role) => role.toLowerCase());
};

export const getPermissionCodes = (user) => {
  const normalized = normalizeUser(user);
  return normalized.permissions
    .map((permission) => {
      if (typeof permission === 'string') return permission;
      return permission?.code || permission?.name || '';
    })
    .filter(Boolean)
    .map((permission) => permission.toLowerCase());
};

export const hasAnyRole = (user, allowedRoles = []) => {
  const roles = new Set(getRoleNames(user));
  return allowedRoles.some((role) => roles.has(role.toLowerCase()));
};

export const PERMISSION_ALIASES = {
  'users.manage': ['users.create', 'users.update', 'users.delete'],
  'roles.manage': ['roles.create', 'roles.update', 'roles.delete'],
  'permissions.manage': ['permissions.create', 'permissions.update', 'permissions.delete'],
  'orders.manage': ['orders.create', 'orders.update', 'orders.delete'],
  'reports.manage': ['reports.create', 'reports.update', 'reports.delete', 'reports.generate'],
  'planning.read': ['planning_requests.read'],
  'planning.manage': ['planning.create', 'planning.update', 'planning.delete', 'planning.approve', 'planning.reject', 'planning_requests.create', 'planning_requests.update', 'planning_requests.delete', 'planning_requests.approve', 'planning_requests.reject'],
  'audit.read': ['audit_logs.read'],
  'audit.manage': ['audit_logs.create', 'audit_logs.update', 'audit_logs.delete'],
};

export const hasAnyPermission = (user, allowedPermissions = []) => {
  const permissions = new Set(getPermissionCodes(user));
  const acceptedPermissions = allowedPermissions.flatMap((permission) => {
    const key = permission.toLowerCase();
    return [key, ...(PERMISSION_ALIASES[key] || [])];
  });
  const hasSuperUserPermission = ['users.manage', 'users.create', 'users.update', 'users.delete'].some((item) => permissions.has(item));
  return hasSuperUserPermission || acceptedPermissions.some((permission) => permissions.has(permission.toLowerCase()));
};

export const canOpenProductDashboard = (user) => {
  // Product dashboard is the safe default workspace for authenticated accounts.
  // This explicitly includes Admin, Staff, Viewer, User, and Customer roles.
  const normalized = normalizeUser(user);
  const roles = getRoleNames(normalized);
  return Boolean(normalized.username) && (roles.length === 0 || hasAnyRole(normalized, PRODUCT_DASHBOARD_ROLES));
};

export const canOpenAdminDashboard = (user) => {
  // Customer is intentionally product-only even if it is accidentally given
  // non-admin read permissions in the database.
  if (hasAnyRole(user, PRODUCT_ONLY_ROLES)) return false;

  return (
    hasAnyRole(user, ADMIN_DASHBOARD_ROLES) ||
    hasAnyPermission(user, ['users.manage', 'roles.manage'])
  );
};
