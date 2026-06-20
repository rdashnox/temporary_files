import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { BACKEND_OFFLINE_MESSAGE, LAST_ORDER_NUMBER_KEY, ORDER_CREATED_EVENT, checkBackendHealth, createEntity, deleteEntity, getDatabaseSummary, isAuthRequiredError, isBackendOfflineError, listEntity, updateEntity } from '../api/client.js';

const currency = new Intl.NumberFormat('en-PH', {
  style: 'currency',
  currency: 'PHP',
  maximumFractionDigits: 0,
});

const statusOptions = {
  orders: ['NEW', 'PAID', 'PACKED', 'SHIPPED', 'COMPLETED', 'CANCELLED', 'EXCEPTION'],
  reports: ['QUEUED', 'RUNNING', 'READY', 'FAILED'],
  'planning-requests': ['DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'CANCELLED'],
  'audit-logs': ['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'PASSWORD_RESET', 'VERIFY_EMAIL', 'CHECKOUT'],
};

const entityConfigs = {
  users: {
    label: 'Users',
    icon: '👥',
    permission: 'users.read',
    managePermission: 'users.manage',
    description: 'Manage accounts, verification status, and assigned roles.',
    columns: ['username', 'email', 'roles', 'is_active', 'is_verified', 'created_at'],
  },
  roles: {
    label: 'Roles',
    icon: '🛡️',
    permission: 'roles.read',
    managePermission: 'roles.manage',
    description: 'Create access groups and attach permissions. Customer role is product-only and does not open the Admin CRUD dashboard.',
    columns: ['name', 'description', 'permissions', 'is_active', 'user_count'],
  },
  permissions: {
    label: 'Permissions',
    icon: '🔐',
    permission: 'permissions.read',
    managePermission: 'permissions.manage',
    description: 'Maintain granular backend permission codes.',
    columns: ['code', 'name', 'module', 'description'],
  },
  orders: {
    label: 'Orders',
    icon: '🧾',
    permission: 'orders.read',
    managePermission: 'orders.manage',
    description: 'Review customer orders, items, statuses, and totals.',
    columns: ['order_number', 'customer_name', 'status', 'items', 'total', 'created_at'],
  },
  reports: {
    label: 'Reports',
    icon: '📊',
    permission: 'reports.read',
    managePermission: 'reports.manage',
    description: 'Queue, update, and track generated business reports.',
    columns: ['name', 'report_type', 'status', 'file_path', 'created_at'],
  },
  'planning-requests': {
    label: 'Planning Requests',
    icon: '🗓️',
    permission: 'planning.read',
    managePermission: 'planning.manage',
    description: 'Submit, review, approve, or reject planning items.',
    columns: ['request_number', 'title', 'priority', 'status', 'due_date'],
  },
  'audit-logs': {
    label: 'Audit Logs',
    icon: '🧭',
    permission: 'audit.read',
    managePermission: 'audit.manage',
    description: 'Inspect system activity and administrative actions.',
    columns: ['action', 'entity_type', 'entity_id', 'actor_username', 'created_at'],
  },
};

const defaultForms = {
  users: {
    username: '',
    email: '',
    full_name: '',
    password: '',
    is_active: true,
    is_verified: true,
    role_ids: [],
  },
  roles: {
    name: '',
    description: '',
    is_active: true,
    permission_ids: [],
  },
  permissions: {
    code: '',
    name: '',
    module: '',
    description: '',
  },
  orders: {
    customer_name: '',
    delivery_address: '',
    payment_method: 'Cash on Delivery',
    status: 'NEW',
    discount: 0,
    shipping_fee: 0,
    tax: 0,
    items_json: '[{"product_id":1,"product_name":"Starter Package","quantity":1,"unit_price":999}]',
  },
  reports: {
    name: '',
    report_type: 'sales',
    status: 'QUEUED',
    parameters_json: '{}',
    file_path: '',
  },
  'planning-requests': {
    title: '',
    description: '',
    priority: 'normal',
    status: 'SUBMITTED',
    due_date: '',
  },
  'audit-logs': {
    action: 'CREATE',
    entity_type: '',
    entity_id: '',
    detail: '',
    ip_address: '',
    user_agent: '',
  },
};

const fieldLabels = {
  username: 'Username',
  email: 'Email',
  full_name: 'Full name',
  password: 'Password',
  is_active: 'Active',
  is_verified: 'Verified',
  role_ids: 'Roles',
  name: 'Name',
  description: 'Description',
  permission_ids: 'Permissions',
  code: 'Code',
  module: 'Module',
  customer_name: 'Customer name',
  delivery_address: 'Delivery address',
  payment_method: 'Payment method',
  status: 'Status',
  discount: 'Discount',
  shipping_fee: 'Shipping fee',
  tax: 'Tax',
  items_json: 'Order items JSON',
  report_type: 'Report type',
  parameters_json: 'Parameters JSON',
  file_path: 'File path',
  title: 'Title',
  priority: 'Priority',
  due_date: 'Due date',
  action: 'Action',
  entity_type: 'Entity type',
  entity_id: 'Entity ID',
  detail: 'Detail',
  ip_address: 'IP address',
  user_agent: 'User agent',
};

const toDateTimeLocal = (value) => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 16);
};

const formatDate = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
};

const humanize = (value) => value.replace(/_/g, ' ').replace(/\b\w/g, (match) => match.toUpperCase());

const normalizeUser = (user) => {
  if (!user) return { username: 'User', permissions: [], roles: [] };
  if (typeof user === 'string') return { username: user, email: user, permissions: [], roles: [] };
  return {
    ...user,
    roles: Array.isArray(user.roles) ? user.roles : [],
    permissions: Array.isArray(user.permissions) ? user.permissions : [],
  };
};

const roleNames = (roles = []) => roles
  .map((role) => {
    if (typeof role === 'string') return role;
    return role?.name || role?.code || '';
  })
  .filter(Boolean);

const ADMIN_FULL_ACCESS_ROLES = ['admin', 'administrator', 'super admin', 'superadmin', 'super user', 'superuser'];

const permissionAliases = {
  'users.read': ['users.manage'],
  'users.manage': ['users.create', 'users.update', 'users.delete'],
  'roles.read': ['roles.manage'],
  'roles.manage': ['roles.create', 'roles.update', 'roles.delete'],
  'permissions.read': ['permissions.manage'],
  'permissions.manage': ['permissions.create', 'permissions.update', 'permissions.delete'],
  'orders.read': ['orders.manage'],
  'orders.manage': ['orders.create', 'orders.update', 'orders.delete'],
  'reports.read': ['reports.manage'],
  'reports.manage': ['reports.create', 'reports.update', 'reports.delete', 'reports.generate'],
  'planning.read': ['planning_requests.read'],
  'planning.manage': ['planning.create', 'planning.update', 'planning.delete', 'planning.approve', 'planning.reject', 'planning_requests.create', 'planning_requests.update', 'planning_requests.delete', 'planning_requests.approve', 'planning_requests.reject'],
  'audit.read': ['audit_logs.read'],
  'audit_logs.read': ['audit.read', 'audit.manage'],
  'audit.manage': ['audit_logs.create', 'audit_logs.update', 'audit_logs.delete'],
};

const hasPermission = (user, permission) => {
  // Admin/Administrator must be able to see every Admin Dashboard module even
  // when old-role migration did not copy every granular permission row.
  const roles = new Set(roleNames(user?.roles || []).map((role) => role.toLowerCase()));
  if (ADMIN_FULL_ACCESS_ROLES.some((role) => roles.has(role))) return true;

  const permissions = new Set(
    (user?.permissions || []).map((item) => {
      if (typeof item === 'string') return item.toLowerCase();
      return (item?.code || item?.name || '').toLowerCase();
    }),
  );
  const requested = permission.toLowerCase();
  const accepted = [requested, ...(permissionAliases[requested] || [])];
  const hasSuperUserPermission = ['users.manage', 'users.create', 'users.update', 'users.delete'].some((item) => permissions.has(item));
  return hasSuperUserPermission || accepted.some((item) => permissions.has(item));
};

const getVisibleEntities = (user) => {
  const entries = Object.entries(entityConfigs).filter(([, config]) => hasPermission(user, config.permission));
  return entries.length ? entries : [['orders', entityConfigs.orders]];
};

const createEmptyForm = (entity) => JSON.parse(JSON.stringify(defaultForms[entity] || defaultForms.roles));

const ensureArray = (value) => (Array.isArray(value) ? value : []);

const safeString = (value) => (value ?? '').toString();

const normalizePermissionCode = (value) => safeString(value).trim().toLowerCase().replace(/\s+/g, '.');

const makeValidationError = (messages) => {
  const error = new Error(messages.join(' '));
  error.name = 'ValidationError';
  return error;
};

const validateRequiredFields = (payload, requirements) => {
  const missing = requirements
    .filter(([field]) => !safeString(payload[field]).trim())
    .map(([, label]) => label);
  if (missing.length) {
    throw makeValidationError([`Please complete required field(s): ${missing.join(', ')}.`]);
  }
};

const roleHelpCards = [
  {
    name: 'Admin',
    badge: 'Full Access',
    description: 'Can open Admin CRUD and Product Dashboard. Has full access to users, roles, permissions, orders, reports, planning, and audit logs.',
  },
  {
    name: 'Staff',
    badge: 'Operations',
    description: 'Can use the Product Dashboard and handle daily order/planning work based on assigned permissions.',
  },
  {
    name: 'Viewer',
    badge: 'Read Only',
    description: 'Can open the Product Dashboard for product browsing and basic read-only access.',
  },
  {
    name: 'Customer',
    badge: 'Product Only',
    description: 'Can only open the Product Dashboard. This role should not see the Admin CRUD dashboard or Roles tab.',
  },
];


const cleanPayload = (payload) => {
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== '' && value !== undefined),
  );
};

export default function AdminDashboard({ user: rawUser, onLogout, onOpenProducts, canOpenProducts = false, initialEntity = null }) {
  const user = useMemo(() => normalizeUser(rawUser), [rawUser]);
  const permissionSignature = useMemo(
    () => [
      ...(user.permissions || []).map((permission) => {
        if (typeof permission === 'string') return permission;
        return permission?.code || permission?.name || '';
      }),
      ...(user.roles || []).map((role) => {
        if (typeof role === 'string') return role;
        return role?.name || role?.code || '';
      }),
    ].filter(Boolean).sort().join('|'),
    [user.permissions, user.roles],
  );
  const visibleEntities = useMemo(() => getVisibleEntities(user), [user, permissionSignature]);
  const [activeEntity, setActiveEntity] = useState(visibleEntities[0][0]);
  const [records, setRecords] = useState([]);
  const [lookup, setLookup] = useState({ roles: [], permissions: [] });
  const [summary, setSummary] = useState({});
  const [query, setQuery] = useState('');
  const [form, setForm] = useState(() => createEmptyForm(activeEntity));
  const [editingRecord, setEditingRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [backendOnline, setBackendOnline] = useState(null);
  const authStoppedRef = useRef(false);
  const summaryLoadedRef = useRef(false);
  const lookupLoadedRef = useRef(false);

  const config = entityConfigs[activeEntity] || entityConfigs.roles;
  const canManage = hasPermission(user, config.managePermission);

  useEffect(() => {
    if (!initialEntity || !entityConfigs[initialEntity]) return;
    if (!hasPermission(user, entityConfigs[initialEntity].permission)) return;
    setActiveEntity(initialEntity);
    setQuery('');
  }, [initialEntity, user, permissionSignature]);

  const backendOfflineText = `${BACKEND_OFFLINE_MESSAGE} Run: ./start-microservices-local-mysql.ps1 then ./start-frontend.ps1`;

  const stopForAuthError = useCallback((err) => {
    if (!isAuthRequiredError(err)) return false;
    authStoppedRef.current = true;
    setLoading(false);
    setSaving(false);
    setError('Your session expired. Please log in again.');
    return true;
  }, []);

  const resetForm = useCallback((entity = activeEntity) => {
    setEditingRecord(null);
    setForm(createEmptyForm(entity));
    setError('');
    setNotice('');
  }, [activeEntity]);

  const ensureBackendOnline = useCallback(async () => {
    if (backendOnline === true) return true;

    const ok = await checkBackendHealth();
    setBackendOnline(ok);
    if (!ok) {
      setLoading(false);
      setError(backendOfflineText);
    }
    return ok;
  }, [backendOfflineText, backendOnline]);

  const loadLookups = useCallback(async () => {
    if (authStoppedRef.current) return;
    if (!(await ensureBackendOnline())) return;
    try {
      const [roles, permissions] = await Promise.all([
        hasPermission(user, 'roles.read') || hasPermission(user, 'users.read') ? listEntity('roles', { limit: 200 }) : Promise.resolve([]),
        hasPermission(user, 'permissions.read') || hasPermission(user, 'roles.manage') ? listEntity('permissions', { limit: 200 }) : Promise.resolve([]),
      ]);
      setLookup({ roles, permissions });
    } catch (err) {
      if (stopForAuthError(err)) return;
      setLookup((current) => current);
    }
  }, [ensureBackendOnline, stopForAuthError, user]);

  const loadEntity = useCallback(async (entity = activeEntity, search = query) => {
    if (authStoppedRef.current) return;
    if (!(await ensureBackendOnline())) return;

    setLoading(true);
    setError('');
    try {
      let data = await listEntity(entity, { limit: entity === 'audit-logs' ? 100 : 50, search });
      if (entity === 'orders' && Array.isArray(data) && data.length === 0 && !safeString(search).trim()) {
        const lastOrderNumber = typeof window !== 'undefined' ? window.localStorage.getItem(LAST_ORDER_NUMBER_KEY) : '';
        if (lastOrderNumber) {
          const retryData = await listEntity('orders', { limit: 50, search: lastOrderNumber });
          if (Array.isArray(retryData) && retryData.length > 0) data = retryData;
        }
      }
      setRecords(Array.isArray(data) ? data : []);
    } catch (err) {
      if (stopForAuthError(err)) return;
      if (isBackendOfflineError(err)) setBackendOnline(false);
      setError(err.message || `Unable to load ${entityConfigs[entity].label}.`);
    } finally {
      setLoading(false);
    }
  }, [activeEntity, ensureBackendOnline, query, stopForAuthError]);

  const loadSummary = useCallback(async () => {
    if (authStoppedRef.current) return;
    if (!(await ensureBackendOnline())) return;

    try {
      const counts = await getDatabaseSummary();
      if (!authStoppedRef.current) {
        setSummary((current) => ({ ...current, ...counts }));
      }
    } catch (err) {
      if (stopForAuthError(err)) return;
      if (isBackendOfflineError(err)) setBackendOnline(false);
      setSummary((current) => ({
        ...current,
        users: current.users ?? '—',
        orders: current.orders ?? '—',
        reports: current.reports ?? '—',
        'audit-logs': current['audit-logs'] ?? '—',
      }));
    }
  }, [ensureBackendOnline, stopForAuthError]);

  useEffect(() => {
    const handleOrderCreated = (event) => {
      if (authStoppedRef.current) return;
      const orderNumber = event?.detail?.order_id || event?.detail?.order_number || '';
      setActiveEntity('orders');
      setQuery('');
      setNotice(orderNumber ? `Order ${orderNumber} was created. Reloading Manage Order List...` : 'Order was created. Reloading Manage Order List...');
      loadEntity('orders', '');
      loadSummary();
    };

    window.addEventListener(ORDER_CREATED_EVENT, handleOrderCreated);
    return () => window.removeEventListener(ORDER_CREATED_EVENT, handleOrderCreated);
  }, [loadEntity, loadSummary]);

  useEffect(() => {
    let alive = true;

    const verifyBackend = async () => {
      const ok = await checkBackendHealth();
      if (!alive) return;
      setBackendOnline(ok);
      if (!ok) {
        setLoading(false);
        setError(backendOfflineText);
      }
    };

    verifyBackend();

    return () => {
      alive = false;
    };
  }, [backendOfflineText]);

  useEffect(() => {
    if (!entityConfigs[activeEntity] || !hasPermission(user, entityConfigs[activeEntity].permission)) {
      setActiveEntity(visibleEntities[0][0]);
    }
  }, [activeEntity, user, visibleEntities]);

  useEffect(() => {
    if (backendOnline !== true) return;
    resetForm(activeEntity);
    loadEntity(activeEntity, '');
  }, [activeEntity, backendOnline]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (backendOnline !== true || authStoppedRef.current) return;

    if (!lookupLoadedRef.current) {
      lookupLoadedRef.current = true;
      loadLookups();
    }

    if (!summaryLoadedRef.current) {
      summaryLoadedRef.current = true;
      loadSummary();
    }
  }, [backendOnline, loadLookups, loadSummary]);

  useEffect(() => {
    if (backendOnline !== true || authStoppedRef.current) return undefined;

    const timer = window.setInterval(() => {
      if (!authStoppedRef.current) loadSummary();
    }, 30000);

    return () => window.clearInterval(timer);
  }, [backendOnline, loadSummary]);

  const handleSearch = async (event) => {
    event.preventDefault();
    loadEntity(activeEntity, query);
  };

  const handleEntityChange = (entity) => {
    setQuery('');
    setRecords([]);
    setEditingRecord(null);
    setForm(createEmptyForm(entity));
    setError('');
    setNotice('');
    setActiveEntity(entity);
  };

  const updateFormField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const buildPayload = () => {
    if (activeEntity === 'orders') {
      let items = [];
      try {
        items = form.items_json.trim() ? JSON.parse(form.items_json) : [];
      } catch {
        throw makeValidationError(['Order items JSON is invalid. Use a JSON array with product_id, product_name, quantity, and unit_price.']);
      }
      if (!Array.isArray(items)) {
        throw makeValidationError(['Order items JSON must be an array.']);
      }
      const payload = cleanPayload({
        customer_name: safeString(form.customer_name).trim(),
        delivery_address: safeString(form.delivery_address).trim(),
        payment_method: safeString(form.payment_method).trim() || 'Cash on Delivery',
        status: safeString(form.status).trim().toUpperCase() || 'NEW',
        discount: Number(form.discount || 0),
        shipping_fee: Number(form.shipping_fee || 0),
        tax: Number(form.tax || 0),
        items: items.map((item) => ({
          product_id: Number(item.product_id),
          product_name: safeString(item.product_name || item.name).trim(),
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price),
        })),
      });
      validateRequiredFields(payload, [['customer_name', 'Customer name'], ['delivery_address', 'Delivery address']]);
      return payload;
    }

    if (activeEntity === 'reports') {
      return cleanPayload({
        name: form.name,
        report_type: form.report_type,
        status: form.status,
        parameters: form.parameters_json.trim() ? JSON.parse(form.parameters_json) : {},
        file_path: form.file_path,
      });
    }

    if (activeEntity === 'planning-requests') {
      return cleanPayload({
        title: form.title,
        description: form.description,
        priority: form.priority,
        status: form.status,
        due_date: form.due_date ? new Date(form.due_date).toISOString() : undefined,
      });
    }

    if (activeEntity === 'users') {
      const payload = cleanPayload({
        username: safeString(form.username).trim(),
        email: safeString(form.email).trim(),
        full_name: safeString(form.full_name).trim(),
        password: form.password,
        is_active: Boolean(form.is_active),
        is_verified: Boolean(form.is_verified),
        role_ids: ensureArray(form.role_ids).map(Number).filter(Boolean),
      });
      if (editingRecord && !form.password) delete payload.password;
      validateRequiredFields(payload, editingRecord ? [['username', 'Username']] : [['username', 'Username'], ['password', 'Password']]);
      return payload;
    }

    if (activeEntity === 'roles') {
      const payload = cleanPayload({
        name: safeString(form.name).trim(),
        description: safeString(form.description).trim(),
        is_active: Boolean(form.is_active),
        permission_ids: ensureArray(form.permission_ids).map(Number).filter(Boolean),
      });
      validateRequiredFields(payload, [['name', 'Name']]);
      return payload;
    }

    if (activeEntity === 'permissions') {
      const code = normalizePermissionCode(form.code);
      const fallbackName = code ? humanize(code) : '';
      const fallbackModule = code.includes('.') ? code.split('.')[0] : code;
      const payload = cleanPayload({
        code,
        name: safeString(form.name).trim() || fallbackName,
        module: safeString(form.module).trim().toLowerCase() || fallbackModule,
        description: safeString(form.description).trim(),
      });
      validateRequiredFields(payload, [['code', 'Code']]);
      return payload;
    }

    return cleanPayload(form);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canManage) return;
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const payload = buildPayload();
      if (editingRecord) {
        await updateEntity(activeEntity, editingRecord.id, payload);
        setNotice(`${config.label.slice(0, -1) || config.label} updated successfully.`);
      } else {
        await createEntity(activeEntity, payload);
        setNotice(`${config.label.slice(0, -1) || config.label} created successfully.`);
      }
      resetForm(activeEntity);
      await loadEntity(activeEntity, query);
      await loadLookups();
      await loadSummary();
    } catch (err) {
      if (stopForAuthError(err)) return;
      setError(err.message || 'Unable to save record. Check required fields and try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    setNotice('');
    setError('');
    if (activeEntity === 'users') {
      setForm({
        username: record.username || '',
        email: record.email || '',
        full_name: record.full_name || '',
        password: '',
        is_active: Boolean(record.is_active),
        is_verified: Boolean(record.is_verified),
        role_ids: record.role_ids || [],
      });
      return;
    }
    if (activeEntity === 'roles') {
      setForm({
        name: record.name || '',
        description: record.description || '',
        is_active: Boolean(record.is_active),
        permission_ids: record.permission_ids || [],
      });
      return;
    }
    if (activeEntity === 'orders') {
      setForm({
        customer_name: record.customer_name || '',
        delivery_address: record.delivery_address || '',
        payment_method: record.payment_method || 'Cash on Delivery',
        status: record.status || 'NEW',
        discount: record.discount || 0,
        shipping_fee: record.shipping_fee || 0,
        tax: record.tax || 0,
        items_json: JSON.stringify(
          (record.items || []).map((item) => ({
            product_id: item.product_id,
            product_name: item.product_name,
            quantity: item.quantity,
            unit_price: item.unit_price,
          })),
          null,
          2,
        ),
      });
      return;
    }
    if (activeEntity === 'reports') {
      setForm({
        name: record.name || '',
        report_type: record.report_type || '',
        status: record.status || 'QUEUED',
        parameters_json: JSON.stringify(record.parameters || {}, null, 2),
        file_path: record.file_path || '',
      });
      return;
    }
    if (activeEntity === 'planning-requests') {
      setForm({
        title: record.title || '',
        description: record.description || '',
        priority: record.priority || 'normal',
        status: record.status || 'SUBMITTED',
        due_date: toDateTimeLocal(record.due_date),
      });
      return;
    }
    if (activeEntity === 'permissions') {
      setForm({
        code: record.code || '',
        name: record.name || '',
        module: record.module || '',
        description: record.description || '',
      });
      return;
    }
    setForm({ ...createEmptyForm(activeEntity), ...record });
  };

  const handleDelete = async (record) => {
    const ok = window.confirm(`Delete/deactivate this ${config.label.toLowerCase()} record?`);
    if (!ok) return;
    setError('');
    setNotice('');
    try {
      await deleteEntity(activeEntity, record.id);
      setNotice('Record removed successfully.');
      await loadEntity(activeEntity, query);
      await loadLookups();
      await loadSummary();
    } catch (err) {
      if (stopForAuthError(err)) return;
      setError(err.message || 'Unable to delete record.');
    }
  };

  const renderValue = (record, column) => {
    if (column === 'created_at' || column === 'updated_at' || column === 'due_date') return formatDate(record[column]);
    if (column === 'roles') return (record.roles || []).map((role) => role.name || role).join(', ') || '—';
    if (column === 'permissions') {
      return (record.permissions || [])
        .slice(0, 6)
        .map((permission) => (typeof permission === 'string' ? permission : permission?.code || permission?.name || 'Permission'))
        .join(', ') || '—';
    }
    if (column === 'items') return `${record.items?.length || 0} item(s)`;
    if (column === 'total') return currency.format(record.total || 0);
    if (typeof record[column] === 'boolean') return record[column] ? 'Yes' : 'No';
    return record[column] || '—';
  };

  const renderField = (field) => {
    const value = form[field];
    const label = fieldLabels[field] || humanize(field);

    if (field === 'role_ids') {
      return (
        <label key={field} className="admin-form-field span-2">
          <span>{label}</span>
          <select multiple value={ensureArray(value).map(String)} onChange={(event) => updateFormField(field, Array.from(event.target.selectedOptions).map((option) => Number(option.value)).filter(Boolean))}>
            {lookup.roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
          </select>
          <small>Hold Ctrl while selecting multiple roles.</small>
        </label>
      );
    }

    if (field === 'permission_ids') {
      return (
        <label key={field} className="admin-form-field span-2">
          <span>{label}</span>
          <select multiple value={ensureArray(value).map(String)} onChange={(event) => updateFormField(field, Array.from(event.target.selectedOptions).map((option) => Number(option.value)).filter(Boolean))}>
            {lookup.permissions.map((permission) => <option key={permission.id} value={permission.id}>{permission.code}</option>)}
          </select>
          <small>Hold Ctrl while selecting multiple permissions.</small>
        </label>
      );
    }

    if (field === 'status' && statusOptions[activeEntity]) {
      return (
        <label key={field} className="admin-form-field">
          <span>{label}</span>
          <select value={safeString(value)} onChange={(event) => updateFormField(field, event.target.value)}>
            {statusOptions[activeEntity].map((option) => <option key={option} value={option}>{humanize(option)}</option>)}
          </select>
        </label>
      );
    }

    if (field === 'action') {
      return (
        <label key={field} className="admin-form-field">
          <span>{label}</span>
          <select value={safeString(value)} onChange={(event) => updateFormField(field, event.target.value)}>
            {statusOptions['audit-logs'].map((option) => <option key={option} value={option}>{humanize(option)}</option>)}
          </select>
        </label>
      );
    }

    if (['is_active', 'is_verified'].includes(field)) {
      return (
        <label key={field} className="admin-check-field">
          <input type="checkbox" checked={Boolean(value)} onChange={(event) => updateFormField(field, event.target.checked)} />
          <span>{label}</span>
        </label>
      );
    }

    if (['description', 'items_json', 'parameters_json', 'detail', 'user_agent'].includes(field)) {
      return (
        <label key={field} className="admin-form-field span-2">
          <span>{label}</span>
          <textarea value={safeString(value)} onChange={(event) => updateFormField(field, event.target.value)} />
        </label>
      );
    }

    const inputType = field.includes('password') ? 'password' : field.includes('date') ? 'datetime-local' : ['discount', 'shipping_fee', 'tax'].includes(field) ? 'number' : 'text';
    return (
      <label key={field} className="admin-form-field">
        <span>{label}</span>
        <input type={inputType} value={safeString(value)} min={inputType === 'number' ? '0' : undefined} step={inputType === 'number' ? '0.01' : undefined} onChange={(event) => updateFormField(field, inputType === 'number' ? event.target.value : event.target.value)} placeholder={editingRecord && field === 'password' ? 'Leave blank to keep current password' : ''} />
      </label>
    );
  };

  const formFields = Object.keys(defaultForms[activeEntity] || defaultForms.roles);
  const stats = [
    ['Users', summary.users ?? '—'],
    ['Orders', summary.orders ?? '—'],
    ['Reports', summary.reports ?? '—'],
    ['Audit Logs', summary['audit-logs'] ?? '—'],
  ];

  return (
    <main className="admin-shell">
      <aside className="admin-sidebar glass-card">
        <div>
          <div className="brand-lockup">
            <div className="brand-symbol">F</div>
            <div>
              <strong>FinMark Admin</strong>
              <span>Database CRUD Console</span>
            </div>
          </div>

          {canOpenProducts && (
            <button className="primary-btn admin-product-switch" type="button" onClick={onOpenProducts}>
              🛒 Product Dashboard
            </button>
          )}

          <nav className="admin-nav" aria-label="Admin modules">
            {visibleEntities.map(([entity, item]) => (
              <button key={entity} type="button" className={entity === activeEntity ? 'active' : ''} onClick={() => handleEntityChange(entity)}>
                <span>{item.icon}</span>
                <b>{item.label}</b>
              </button>
            ))}
          </nav>
        </div>

        <div className="admin-user-card">
          <div className="profile-avatar">{user.username?.[0]?.toUpperCase() || 'U'}</div>
          <div>
            <strong>{user.full_name || user.username}</strong>
            <span>{roleNames(user.roles).join(', ') || 'Authenticated user'}</span>
          </div>
          <button className="logout-btn" onClick={onLogout}>Logout</button>
        </div>
      </aside>

      <section className="admin-main">
        <header className="admin-hero glass-card">
          <div>
            <p className="eyebrow">Admin Dashboard</p>
            <h1>Manage {config.label}</h1>
            <p>{config.description}</p>
          </div>
          <div className="admin-hero-actions">
            {canOpenProducts && <button className="light-btn" type="button" onClick={onOpenProducts}>Open Product Dashboard</button>}
            <button className="light-btn" type="button" onClick={async () => {
              const ok = await checkBackendHealth();
              setBackendOnline(ok);
              if (!ok) {
                setError(backendOfflineText);
                return;
              }
              authStoppedRef.current = false;
              lookupLoadedRef.current = true;
              summaryLoadedRef.current = true;
              loadEntity(activeEntity, query);
              loadLookups();
              loadSummary();
            }}>Refresh</button>
            <button className="primary-btn" type="button" onClick={() => resetForm(activeEntity)} disabled={!canManage}>+ New record</button>
          </div>
        </header>


        {activeEntity === 'roles' && (
          <section className="role-guide-grid" aria-label="Role dashboard guide">
            {roleHelpCards.map((role) => (
              <article className="role-guide-card glass-card" key={role.name}>
                <div>
                  <span>{role.badge}</span>
                  <h3>{role.name}</h3>
                </div>
                <p>{role.description}</p>
              </article>
            ))}
          </section>
        )}

        <section className="admin-stats-grid">
          {stats.map(([label, value]) => (
            <article className="admin-stat glass-card" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
              <small>Real MySQL row count</small>
            </article>
          ))}
        </section>

        {backendOnline === false && (
          <section className="backend-offline-banner glass-card">
            <div>
              <strong>Backend API is offline</strong>
              <p>The Admin Dashboard needs FastAPI running on <code>http://127.0.0.1:8000</code>. Start the backend, then click Check again.</p>
              <code>python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000</code>
            </div>
            <button className="primary-btn" type="button" onClick={async () => {
              const ok = await checkBackendHealth();
              setBackendOnline(ok);
              if (ok) {
                setError('');
                await loadEntity(activeEntity, query);
                await loadLookups();
                await loadSummary();
              } else {
                setError(backendOfflineText);
              }
            }}>Check again</button>
          </section>
        )}

        <section className="admin-workspace">
          <article className="admin-panel glass-card">
            <div className="admin-panel-head">
              <div>
                <h2>{editingRecord ? `Edit ${config.label}` : `Create ${config.label}`}</h2>
                <p>{canManage ? 'Use this form to create or update database records.' : 'You can view this module, but your role cannot modify records.'}</p>
              </div>
            </div>

            {error && <p className="message error">{error}</p>}
            {notice && <p className="message success">{notice}</p>}

            <form className="admin-form" onSubmit={handleSubmit}>
              {formFields.map(renderField)}
              <div className="admin-form-actions span-2">
                <button className="primary-btn" type="submit" disabled={!canManage || saving}>{saving ? 'Saving...' : editingRecord ? 'Save changes' : 'Create record'}</button>
                <button className="light-btn" type="button" onClick={() => resetForm(activeEntity)}>Clear</button>
              </div>
            </form>
          </article>

          <article className="admin-panel glass-card">
            <div className="admin-panel-head">
              <div>
                <h2>{config.label} List</h2>
                <p>{records.length} record(s) loaded.</p>
              </div>
              <form className="admin-search" onSubmit={handleSearch}>
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${config.label.toLowerCase()}...`} />
                <button className="light-btn" type="submit">Search</button>
              </form>
            </div>

            {error && (
              <div className="state-card error-text">{error}</div>
            )}

            {activeEntity === 'roles' && !loading && !error && (
              <div className="roles-readiness-card">
                <strong>Roles module loaded</strong>
                <span>Use this tab to create access groups, attach permissions, and confirm that Customer stays product-only.</span>
              </div>
            )}

            {loading ? (
              <div className="state-card">Loading records...</div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      {config.columns.map((column) => <th key={column}>{humanize(column)}</th>)}
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id}>
                        <td>#{record.id}</td>
                        {config.columns.map((column) => <td key={column}>{renderValue(record, column)}</td>)}
                        <td>
                          <div className="table-actions">
                            <button className="light-btn small" type="button" onClick={() => handleEdit(record)} disabled={!canManage}>Edit</button>
                            <button className="light-btn small danger" type="button" onClick={() => handleDelete(record)} disabled={!canManage}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!records.length && (
                      <tr>
                        <td colSpan={config.columns.length + 2}>
                          No {config.label.toLowerCase()} found. {query ? 'Try clearing the search keyword.' : canManage ? 'Create one using the form on the left.' : 'Your account can view this module, but no records are available yet.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </article>
        </section>
      </section>
    </main>
  );
}
