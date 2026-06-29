-- FinMark Enterprise Auth Migration Verification
-- Run this in MySQL Workbench after migrate-legacy-auth-to-enterprise.ps1.

SELECT 'Auth users' AS item, COUNT(*) AS total FROM finmark_auth_db.auth_users
UNION ALL
SELECT 'Auth roles', COUNT(*) FROM finmark_auth_db.auth_roles
UNION ALL
SELECT 'Auth permissions', COUNT(*) FROM finmark_auth_db.auth_permissions
UNION ALL
SELECT 'User-role links', COUNT(*) FROM finmark_auth_db.auth_user_roles
UNION ALL
SELECT 'Role-permission links', COUNT(*) FROM finmark_auth_db.auth_role_permissions;

SELECT id, username, email, full_name, is_active, is_verified, created_at
FROM finmark_auth_db.auth_users
ORDER BY id
LIMIT 50;

SELECT r.name AS role_name, COUNT(rp.permission_id) AS permission_count
FROM finmark_auth_db.auth_roles r
LEFT JOIN finmark_auth_db.auth_role_permissions rp ON rp.role_id = r.id
GROUP BY r.id, r.name
ORDER BY r.name;

SELECT u.email, r.name AS role_name
FROM finmark_auth_db.auth_users u
JOIN finmark_auth_db.auth_user_roles ur ON ur.user_id = u.id
JOIN finmark_auth_db.auth_roles r ON r.id = ur.role_id
ORDER BY u.email, r.name;

SELECT p.code, p.module
FROM finmark_auth_db.auth_permissions p
WHERE p.code IN (
  'users.manage',
  'roles.manage',
  'permissions.manage',
  'inventory.read',
  'inventory.manage',
  'dashboard.admin',
  'dashboard.products',
  'product_dashboard.access'
)
ORDER BY p.code;
