# FinMark 4 Dedicated MySQL Database Setup for MySQL Workbench

This guide sets up the full enterprise microservice database layout so you can show the databases in **MySQL Workbench**.

## Target Database Layout

| Microservice | Dedicated MySQL Database |
|---|---|
| Auth/Login Service | `finmark_auth_db` |
| Order Service | `finmark_order_db` |
| Inventory Service | `finmark_inventory_db` |
| Notification Service | `finmark_notification_db` |

The application user created for the microservices is:

```text
Username: finmark_app
Password: FinmarkApp@2026!
```

For production, change this password and update the `.env` database URLs.

---

## Recommended Setup: One PowerShell Command

From the project root, run:

```powershell
.\setup-enterprise-mysql.ps1
```

The script will:

1. connect to MySQL using your root/admin account;
2. create the four dedicated databases;
3. create the `finmark_app` database user;
4. grant access only to the four FinMark databases;
5. update `.env` with the four database URLs;
6. install missing Python dependencies;
7. run Alembic migrations to create tables;
8. seed demo data for login and inventory;
9. make the databases visible in MySQL Workbench.

After it finishes, open **MySQL Workbench**, right-click the **SCHEMAS** panel, then choose **Refresh All**.

---

## Manual MySQL Workbench Setup

Use this if `mysql.exe` is not available in PowerShell.

1. Open **MySQL Workbench**.
2. Connect as `root` or another MySQL admin user.
3. Open this file:

```text
setup-4-dedicated-databases-workbench.sql
```

4. Execute the full script using the lightning button.
5. Refresh the **SCHEMAS** panel.
6. Confirm that these four databases appear:

```text
finmark_auth_db
finmark_order_db
finmark_inventory_db
finmark_notification_db
```

Then run the migrations from PowerShell:

```powershell
.\run-enterprise-migrations-mysql.ps1
```

Then verify:

```powershell
.\verify-enterprise-mysql-databases.ps1
```

---

## Start Microservices Using MySQL Databases

After setup, start the no-Docker microservices using the MySQL databases:

```powershell
.\start-microservices-local-mysql.ps1
```

This starts:

| Service | Replica Ports |
|---|---|
| Auth Service | 8101, 8102, 8103 or fallback ports |
| Order Service | 8201, 8202, 8203 or fallback ports |
| Inventory Service | 8301, 8302, 8303 or fallback ports |
| Notification Service | 8401, 8402, 8403 or fallback ports |
| Local API Gateway | 8000 or fallback port |

---

## How to Show It in MySQL Workbench

In MySQL Workbench, show the **SCHEMAS** list and point to these databases:

```text
finmark_auth_db
finmark_order_db
finmark_inventory_db
finmark_notification_db
```

Then expand each database to show its tables.

Expected examples:

- `finmark_auth_db`: users, roles, permissions, audit logs
- `finmark_order_db`: orders, order items, outbox events
- `finmark_inventory_db`: products, inventory outbox events
- `finmark_notification_db`: notifications, inbox events

This proves that the microservices are using **database-per-service architecture**.

---

## Useful Verification Commands

Verify databases and table counts:

```powershell
.\verify-enterprise-mysql-databases.ps1
```

Run only migrations again:

```powershell
.\run-enterprise-migrations-mysql.ps1
```

Start the local microservices with MySQL:

```powershell
.\start-microservices-local-mysql.ps1
```

Demo admin login:

```text
Email: admin@example.com
Password: Admin@12345
```
