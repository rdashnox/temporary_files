-- Fix for: pymysql.err.OperationalError: (1045, "Access denied for user ...")
-- Run this in MySQL Workbench using an account that can create users and grant privileges.
-- After running it, use the separated DB_* values shown at the bottom of this file.

CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp123';
CREATE USER IF NOT EXISTS 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp123';

ALTER USER 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp123';
ALTER USER 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp123';

GRANT ALL PRIVILEGES ON finmark_db.* TO 'finmark_app'@'localhost';
GRANT ALL PRIVILEGES ON finmark_db.* TO 'finmark_app'@'127.0.0.1';

FLUSH PRIVILEGES;

-- Use these in your project-level .env file:
-- DB_DRIVER=mysql+pymysql
-- DB_HOST=127.0.0.1
-- DB_PORT=3306
-- DB_NAME=finmark_db
-- DB_USER=finmark_app
-- DB_PASSWORD=FinmarkApp123
