-- =========================================================
-- FinMark Roles Tab + Customer Product-Only Refactor
-- Run this in MySQL Workbench after your main schema/seed scripts.
-- Safe to run multiple times.
-- =========================================================

USE finmark_db;

SET @OLD_SQL_SAFE_UPDATES = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;

START TRANSACTION;

-- Keep Admin compatible with both old *.manage and new granular permissions.
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
  ('dashboard.products.read', 'View Product Dashboard', 'dashboard', 'Can open the Product Dashboard and browse products.', NOW())
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

INSERT INTO roles (name, description, is_active, created_at, updated_at)
VALUES
  ('Customer', 'Product-only customer role. Opens Product Dashboard only and does not access Admin CRUD.', 1, NOW(), NOW()),
  ('Viewer', 'Read-only dashboard role.', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = NOW();

INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p
WHERE r.name = 'Admin'
  AND p.code IN (
    'roles.read', 'roles.create', 'roles.update', 'roles.delete',
    'permissions.read', 'permissions.create', 'permissions.update', 'permissions.delete',
    'audit_logs.read', 'dashboard.products.read'
  );

INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code = 'dashboard.products.read'
WHERE r.name = 'Customer';

-- Customer dummy user:
-- Email: customer@example.com
-- Password: Customer123!
INSERT INTO users (
  username, email, hashed_password, full_name, is_active, is_verified,
  verification_token, verification_token_expires_at,
  password_reset_token, password_reset_token_expires_at,
  last_login_at, created_at, updated_at
)
VALUES (
  'customer@example.com',
  'customer@example.com',
  '$2b$12$X05m1qLj6t6qgMvM/f2..uGxPcdmQs3J3ybMYH5Gam5tzZeyRCZYa',
  'Demo Customer',
  1,
  1,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NOW(),
  NOW()
)
ON DUPLICATE KEY UPDATE
  hashed_password = VALUES(hashed_password),
  full_name = VALUES(full_name),
  is_active = VALUES(is_active),
  is_verified = VALUES(is_verified),
  updated_at = NOW();

INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Customer'
WHERE u.email = 'customer@example.com';

-- Safety cleanup: Customer must not have Admin CRUD permissions.
DELETE rp
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE r.name = 'Customer'
  AND (
    p.code LIKE 'users.%'
    OR p.code LIKE 'roles.%'
    OR p.code LIKE 'permissions.%'
    OR p.code LIKE 'audit_logs.%'
    OR p.code IN ('users.manage', 'roles.manage', 'permissions.manage', 'audit.read', 'audit.manage')
  );

COMMIT;

SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;

SELECT r.name AS role_name, r.description, r.is_active, COUNT(rp.permission_id) AS permission_count
FROM roles r
LEFT JOIN role_permissions rp ON rp.role_id = r.id
WHERE r.name IN ('Admin', 'Staff', 'Viewer', 'Customer')
GROUP BY r.id, r.name, r.description, r.is_active
ORDER BY r.name;

SELECT u.email, GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ', ') AS roles
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
WHERE u.email IN ('customer@example.com', 'admin@example.com', 'staff@example.com', 'viewer@example.com', 'user@example.com')
GROUP BY u.id, u.email
ORDER BY u.email;
