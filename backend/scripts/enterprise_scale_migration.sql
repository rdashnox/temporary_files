-- Enterprise scale migration for an existing FinMark MySQL database.
-- Run this once before deploying the 1,000-active-user version.
-- Designed to be safe to re-run on MySQL 8.x.

USE finmark_db;

-- Retry-safe checkout support. MySQL allows multiple NULL values in a UNIQUE column.
SET @column_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'orders'
      AND COLUMN_NAME = 'idempotency_key'
);
SET @sql := IF(
    @column_exists = 0,
    'ALTER TABLE orders ADD COLUMN idempotency_key VARCHAR(120) NULL',
    'SELECT "orders.idempotency_key already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'orders'
      AND INDEX_NAME = 'ix_orders_idempotency_key'
);
SET @sql := IF(
    @index_exists = 0,
    'CREATE UNIQUE INDEX ix_orders_idempotency_key ON orders (idempotency_key)',
    'SELECT "ix_orders_idempotency_key already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'orders'
      AND INDEX_NAME = 'ix_orders_status_created_at'
);
SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX ix_orders_status_created_at ON orders (status, created_at)',
    'SELECT "ix_orders_status_created_at already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'orders'
      AND INDEX_NAME = 'ix_orders_user_created_at'
);
SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX ix_orders_user_created_at ON orders (user_id, created_at)',
    'SELECT "ix_orders_user_created_at already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @index_exists := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'notifications'
      AND INDEX_NAME = 'ix_notifications_user_created_at'
);
SET @sql := IF(
    @index_exists = 0,
    'CREATE INDEX ix_notifications_user_created_at ON notifications (user_id, created_at)',
    'SELECT "ix_notifications_user_created_at already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
