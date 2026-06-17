-- =========================================================
-- FinMark Customer Product-Only Role Seed
-- Purpose: add a Customer role and demo customer user.
-- Customer should open Product Dashboard only, not Admin CRUD.
-- Safe to run multiple times in MySQL Workbench.
-- =========================================================

USE finmark_db;

START TRANSACTION;

INSERT INTO roles (name, description, is_active, created_at, updated_at)
VALUES ('Customer', 'Product-only customer role. Opens Product Dashboard only and does not access Admin CRUD.', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  is_active = VALUES(is_active),
  updated_at = NOW();

-- Optional marker permission for dashboard access. This is not an admin permission.
INSERT INTO permissions (code, name, module, description, created_at)
VALUES ('dashboard.products.read', 'View Product Dashboard', 'dashboard', 'Can open the Product Dashboard and browse products.', NOW())
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  module = VALUES(module),
  description = VALUES(description);

INSERT IGNORE INTO role_permissions (role_id, permission_id, assigned_at)
SELECT r.id, p.id, NOW()
FROM roles r
JOIN permissions p ON p.code = 'dashboard.products.read'
WHERE r.name = 'Customer';

-- Dummy customer account:
-- Email: customer@example.com
-- Password: Customer123!
INSERT INTO users (
  username,
  email,
  hashed_password,
  full_name,
  is_active,
  is_verified,
  verification_token,
  verification_token_expires_at,
  password_reset_token,
  password_reset_token_expires_at,
  last_login_at,
  created_at,
  updated_at
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
  verification_token = NULL,
  verification_token_expires_at = NULL,
  password_reset_token = NULL,
  password_reset_token_expires_at = NULL,
  updated_at = NOW();

-- Make sure customer@example.com has Customer role.
INSERT IGNORE INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u
JOIN roles r ON r.name = 'Customer'
WHERE u.email = 'customer@example.com';

-- Safety cleanup: Customer role must not have Admin CRUD permissions.
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

SELECT u.email, GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ', ') AS roles
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
WHERE u.email = 'customer@example.com'
GROUP BY u.id, u.email;

SELECT r.name AS role_name, GROUP_CONCAT(p.code ORDER BY p.code SEPARATOR ', ') AS permissions
FROM roles r
LEFT JOIN role_permissions rp ON rp.role_id = r.id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE r.name = 'Customer'
GROUP BY r.id, r.name;
