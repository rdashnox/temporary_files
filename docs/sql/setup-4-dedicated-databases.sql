-- FinMark Enterprise Microservices - 4 Dedicated MySQL Database Setup
-- Run this file in MySQL Workbench using an admin/root connection.
-- After running it, refresh the SCHEMAS panel. You should see:
--   finmark_auth_db
--   finmark_order_db
--   finmark_inventory_db
--   finmark_notification_db
--
-- This script creates the databases and a least-privilege application user.
-- The Alembic migration command creates the tables after the databases exist.

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

-- Dedicated application user for the enterprise microservices.
-- The setup-enterprise-mysql.ps1 script replaces these placeholders automatically.
-- If you run this directly in Workbench, replace the placeholders first.
CREATE USER IF NOT EXISTS '__FINMARK_APP_USER__'@'localhost' IDENTIFIED BY '__FINMARK_APP_PASSWORD__';
CREATE USER IF NOT EXISTS '__FINMARK_APP_USER__'@'127.0.0.1' IDENTIFIED BY '__FINMARK_APP_PASSWORD__';

ALTER USER '__FINMARK_APP_USER__'@'localhost' IDENTIFIED BY '__FINMARK_APP_PASSWORD__';
ALTER USER '__FINMARK_APP_USER__'@'127.0.0.1' IDENTIFIED BY '__FINMARK_APP_PASSWORD__';

GRANT ALL PRIVILEGES ON finmark_auth_db.* TO '__FINMARK_APP_USER__'@'localhost';
GRANT ALL PRIVILEGES ON finmark_order_db.* TO '__FINMARK_APP_USER__'@'localhost';
GRANT ALL PRIVILEGES ON finmark_inventory_db.* TO '__FINMARK_APP_USER__'@'localhost';
GRANT ALL PRIVILEGES ON finmark_notification_db.* TO '__FINMARK_APP_USER__'@'localhost';

GRANT ALL PRIVILEGES ON finmark_auth_db.* TO '__FINMARK_APP_USER__'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_order_db.* TO '__FINMARK_APP_USER__'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_inventory_db.* TO '__FINMARK_APP_USER__'@'127.0.0.1';
GRANT ALL PRIVILEGES ON finmark_notification_db.* TO '__FINMARK_APP_USER__'@'127.0.0.1';

FLUSH PRIVILEGES;

-- Verification query for MySQL Workbench.
SELECT SCHEMA_NAME AS created_database
FROM INFORMATION_SCHEMA.SCHEMATA
WHERE SCHEMA_NAME IN (
  'finmark_auth_db',
  'finmark_order_db',
  'finmark_inventory_db',
  'finmark_notification_db'
)
ORDER BY SCHEMA_NAME;
