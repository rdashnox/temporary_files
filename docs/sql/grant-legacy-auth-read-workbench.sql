-- FinMark Legacy Auth Read Grant
-- Run this in MySQL Workbench as root/admin only if you want finmark_app
-- to read users/roles/permissions from the old monolith database finmark_db.

CREATE USER IF NOT EXISTS 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp@2026!';
CREATE USER IF NOT EXISTS 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp@2026!';

GRANT SELECT ON finmark_db.users TO 'finmark_app'@'localhost';
GRANT SELECT ON finmark_db.roles TO 'finmark_app'@'localhost';
GRANT SELECT ON finmark_db.permissions TO 'finmark_app'@'localhost';
GRANT SELECT ON finmark_db.user_roles TO 'finmark_app'@'localhost';
GRANT SELECT ON finmark_db.role_permissions TO 'finmark_app'@'localhost';

GRANT SELECT ON finmark_db.users TO 'finmark_app'@'127.0.0.1';
GRANT SELECT ON finmark_db.roles TO 'finmark_app'@'127.0.0.1';
GRANT SELECT ON finmark_db.permissions TO 'finmark_app'@'127.0.0.1';
GRANT SELECT ON finmark_db.user_roles TO 'finmark_app'@'127.0.0.1';
GRANT SELECT ON finmark_db.role_permissions TO 'finmark_app'@'127.0.0.1';

FLUSH PRIVILEGES;

SELECT 'finmark_app now has SELECT access to legacy auth tables in finmark_db.' AS result;
