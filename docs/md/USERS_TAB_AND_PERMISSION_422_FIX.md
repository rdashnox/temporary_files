# Users Tab + Permission 422 Fix

This refactor fixes two frontend/backend issues:

1. Clicking the Users tab could show a blank white screen.
2. Creating a permission could return `422 Unprocessable Content`.

## Root causes

### Users tab blank white screen

The admin form was switching modules before the form state was reset. For one render, the Users tab could try to render `role_ids` using an old form object from another module. That caused code like `value.map(...)` to run when `value` was `undefined`, which crashes the React page and produces a blank white screen.

### Permission create 422

The frontend could submit a permission payload with missing or blank `code`, `name`, or `module`. The backend schema required these fields, so FastAPI correctly returned `422 Unprocessable Content`.

## Fixes applied

- Added safe array handling for role and permission multi-select fields.
- Reset form state immediately when changing tabs.
- Added client-side validation before submitting Users, Roles, and Permissions.
- Added auto-fill for permission `name` and `module` based on the permission code.
- Improved frontend API error formatting for FastAPI/Pydantic 422 responses.
- Made backend permission creation more forgiving by deriving missing name/module from the permission code.

## Example permission creation

You can now enter only:

```text
Code: orders.export
```

The app will derive:

```text
Name: Orders Export
Module: orders
```

## Test results

```text
Frontend build: successful
Backend tests: 17 passed
```
