# Python 3.14 SQLAlchemy startup fix

## Problem

The backend failed during startup with:

```text
TypeError: descriptor __getitem__ requires a typing.Union object but received a tuple
```

This happened while SQLAlchemy was scanning ORM type annotations in `backend/models.py`. The project was pinned to `SQLAlchemy==2.0.36`, which predates Python 3.14 support/fixes.

## Fix applied

1. Updated SQLAlchemy in `requirements.txt`:

```text
SQLAlchemy==2.0.49
```

2. Removed Python 3.14-sensitive union annotations from SQLAlchemy model columns and relationships. Nullable database behavior is still controlled by `nullable=True`, so the database schema remains the same.

Example:

```python
# Before
description: Mapped[str | None] = mapped_column(String(255), nullable=True)

# After
description: Mapped[str] = mapped_column(String(255), nullable=True)
```

## Required local commands

From the project root, run:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt --upgrade
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If problems continue on Python 3.14, use Python 3.12 for this school project because it has the broadest dependency compatibility.
