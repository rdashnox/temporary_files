CREATE DATABASE IF NOT EXISTS finmark_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Optional dedicated app user. Change the password before using in real deployments.
CREATE USER IF NOT EXISTS 'finmark_app'@'localhost' IDENTIFIED BY 'FinmarkApp123';
CREATE USER IF NOT EXISTS 'finmark_app'@'127.0.0.1' IDENTIFIED BY 'FinmarkApp123';
GRANT ALL PRIVILEGES ON finmark_db.* TO 'finmark_app'@'localhost';
GRANT ALL PRIVILEGES ON finmark_db.* TO 'finmark_app'@'127.0.0.1';
FLUSH PRIVILEGES;
