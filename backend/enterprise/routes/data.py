from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..security.user_auth import get_current_user

router = APIRouter()


@router.get("/protected")
def read_protected_data(current_user: dict = Depends(get_current_user)):
    return {"message": "This is protected data!", "authenticated_user": current_user["username"]}


@router.get("/business-modules")
def read_business_modules(current_user: dict = Depends(get_current_user)):
    return {
        "metadata": {
            "authenticated_user": current_user["username"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "architecture": "enterprise-microservices-database-per-service",
            "service_databases": ["auth", "order", "inventory", "notification"],
        },
        "summary": {
            "revenue": 1845000,
            "revenueTrend": "+12.8% vs last month",
            "ordersToday": 486,
            "pendingApprovals": 17,
            "riskAlerts": 4,
        },
        "orders": {
            "statuses": [
                {"label": "New", "count": 132, "hint": "Awaiting validation"},
                {"label": "Paid", "count": 184, "hint": "Payment confirmed"},
                {"label": "Packed", "count": 91, "hint": "Warehouse queue"},
                {"label": "Shipped", "count": 62, "hint": "Tracking active"},
                {"label": "Exception", "count": 17, "hint": "Needs review"},
            ],
        },
        "access": {"roles": current_user.get("roles", []), "permissions": current_user.get("permissions", [])},
    }
