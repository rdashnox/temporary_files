# Roles Tab + Customer Product-Only Refactor

## What was fixed

The Roles tab now has visible role guide cards, a readiness notice, safer error/empty states, and hardened rendering for role permissions. If the API has no records or returns an error, the dashboard no longer appears as a blank white page.

## Customer role

A new `Customer` role was added. It is intended for product-only access.

Demo login:

```text
customer@example.com / Customer123!
```

Expected behavior:

- Customer opens the Product Dashboard.
- Customer does not see or open Admin CRUD.
- Customer cannot access `/api/v1/database/roles`.

## SQL seed helper

Run this in MySQL Workbench if your database already exists:

```text
backend/scripts/roles_tab_customer_refactor.sql
```

This script:

- Adds the `Customer` role.
- Adds `customer@example.com`.
- Adds a product dashboard marker permission.
- Removes admin CRUD permissions from the Customer role.
- Aligns Admin role permissions for the Roles tab.

## Routes

```text
Product Dashboard: http://localhost:5173/products
Admin CRUD:        http://localhost:5173/admin
```

## Test result

```text
Backend tests: 17 passed
Frontend build: successful
```
