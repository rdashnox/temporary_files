-- =========================================================
-- FinMark Role/Permission Alignment Fix
-- Purpose: make the Admin Roles/Permissions tabs work with both
-- older *.manage permissions and newer granular *.read/*.create/*.update/*.delete permissions.
-- Safe to run multiple times in MySQL Workbench.
-- =========================================================

USE finmark_db;

START TRANSACTION;

INSERT INTO permissions (code, name, module, description, created_at)
VALUES
  ('roles.read', 'View Roles', 'roles', 'Can view roles in the admin dashboard.', NOW()),
  ('roles.create', 'Create Roles', 'roles', 'Can create roles.', NOW()),
  ('roles.update', 'Update Roles', 'roles', 'Can update roles.', NOW()),
  ('roles.delete', 'Delete Roles', 'roles', 'Can delete or deactivate roles.', NOW()),
  ('permissions.read', 'View Permissions', 'permissions', 'Can view permission codes in the admin dashboard.', NOW()),
  ('permissions.create', 'Create Permissions', 'permissions', 'Can create permission codes.', NOW()),
  ('permissions.update', 'Update Permissions', 'permissions', 'Can update permission codes.', NOW()),
  ('permissions.delete', 'Delete Permissions', 'permissions', 'Can delete permission codes.', NOW()),
  ('audit_logs.read', 'View Audit Logs', 'audit_logs', 'Can view audit logs.', NOW()),
  ('audit_logs.create', 'Create Audit Logs', 'audit_logs', 'Can manually create audit log records.', NOW()),
  ('audit_logs.update', 'Update Audit Logs', 'audit_logs', 'Can update audit log records.', NOW()),
  ('audit_logs.delete', 'Delete Audit Logs', 'audit_logs', 'Can delete audit log records.', NOW())
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

-- Make Admin complete even if it was seeded before the granular permissions existed.
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p
WHERE r.name = 'Admin'
  AND p.code IN (
    'roles.read', 'roles.create', 'roles.update', 'roles.delete',
    'permissions.read', 'permissions.create', 'permissions.update', 'permissions.delete',
    'audit_logs.read', 'audit_logs.create', 'audit_logs.update', 'audit_logs.delete'
  );

-- Make Auditor read-only for access-related tabs.
INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code IN ('roles.read', 'permissions.read', 'audit_logs.read')
WHERE r.name = 'Auditor';

COMMIT;

SELECT r.name AS role_name, GROUP_CONCAT(p.code ORDER BY p.code SEPARATOR ', ') AS permissions
FROM roles r
LEFT JOIN role_permissions rp ON rp.role_id = r.id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE r.name IN ('Admin', 'Auditor')
GROUP BY r.id, r.name
ORDER BY r.name;
