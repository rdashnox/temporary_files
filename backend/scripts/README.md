# SQL Scripts README

Run SQL scripts in **MySQL Workbench** while connected to your local MySQL server.

## Recommended New Database Setup

For a fresh setup, run these in order:

### 1. Main schema and base seed

```text
backend/scripts/schema_and_seed_mysql.sql
```

This creates the main `finmark_db` database tables.

### 2. Latest refactor seed and safe updates

```text
backend/scripts/finmark_refactor_seed_no_values_safe.sql
```

This adds/updates the final roles, permissions, demo accounts, role mappings, product-dashboard permissions, and status normalization.

## Demo Accounts Created

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin123!` |
| Manager | `manager@example.com` | `Manager123!` |
| Staff | `staff@example.com` | `Staff123!` |
| Viewer | `viewer@example.com` | `Viewer123!` |
| Customer | `customer@example.com` | `Customer123!` |
| User | `user@example.com` | `Password123!` |

## Other Scripts

| Script | Use |
|---|---|
| `create_mysql_database.sql` | Creates the database only. Use if you want to create DB before running schema scripts. |
| `fix_mysql_access_denied.sql` | Creates a dedicated MySQL app user if root login causes access denied. |
| `role_permission_alignment.sql` | Aligns older `*.manage` permissions with newer granular permissions. |
| `roles_tab_customer_refactor.sql` | Adds Roles-tab and Customer role improvements to an older database. |
| `customer_role_product_only_seed.sql` | Adds only Customer product-only role and account. |

## Verification Queries

After running scripts, you can check users and roles:

```sql
USE finmark_db;

SELECT u.id, u.email, u.full_name, GROUP_CONCAT(r.name ORDER BY r.name SEPARATOR ', ') AS roles
FROM users u
LEFT JOIN user_roles ur ON ur.user_id = u.id
LEFT JOIN roles r ON r.id = ur.role_id
GROUP BY u.id, u.email, u.full_name
ORDER BY u.id;
```

Check KPI source counts:

```sql
USE finmark_db;

SELECT 'users' AS table_name, COUNT(*) AS total FROM users
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'reports', COUNT(*) FROM reports
UNION ALL SELECT 'audit_logs', COUNT(*) FROM audit_logs;
```
