-- FinMark Enterprise Microservices - MySQL Workbench Direct Setup
-- Use this version if you want to run the setup directly inside MySQL Workbench.
-- It uses the default app user below:
--   Username: finmark_app
--   Password: FinmarkApp@2026!
--
-- Steps:
-- 1. Open MySQL Workbench.
-- 2. Connect as root/admin.
-- 3. Open this file.
-- 4. Click the lightning/execution button.
-- 5. Right-click the SCHEMAS panel and choose Refresh All.

CREATE DATABASE IF NOT EXISTS finmark_auth_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS finmark_order_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS finmark_inventory_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS finmark_notification_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp@2026!';
CREATE USER IF NOT EXISTS 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp@2026!';
ALTER USER 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp@2026!';
ALTER USER 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp@2026!';

GRANT ALL PRIVILEGES ON finmark_auth_db.* TO 'finmark_app'@'localhost';
GRANT ALL PRIVILEGES ON finmark_order_db.* TO 'finmark_app'@'localhost';
GRANT ALL PRIVILEGES ON finmark_inventory_db.* TO 'finmark_app'@'localhost';
GRANT ALL PRIVILEGES ON finmark_notification_db.* TO 'finmark_app'@'localhost';

GRANT ALL PRIVILEGES ON finmark_auth_db.* TO 'finmark_app'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_order_db.* TO 'finmark_app'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_inventory_db.* TO 'finmark_app'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_notification_db.* TO 'finmark_app'@'127.0.0.1';

FLUSH PRIVILEGES;

SELECT SCHEMA_NAME AS created_database
FROM INFORMATION_SCHEMA.SCHEMATA
WHERE SCHEMA_NAME IN (
  'finmark_auth_db',
  'finmark_order_db',
  'finmark_inventory_db',
  'finmark_notification_db'
)
ORDER BY SCHEMA_NAME;
