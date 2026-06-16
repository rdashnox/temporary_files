from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..controllers import auth_controller

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate the bearer token and return the current verified user."""
    user = auth_controller.get_current_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or unverified access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.get("/protected")
async def read_protected_data(current_user: dict = Depends(get_current_user)):
    """Retrieve protected data, requiring a valid signed JWT access token."""
    return {
        "message": "This is protected data!",
        "authenticated_user": current_user["username"],
    }


@router.get("/business-modules")
async def read_business_modules(current_user: dict = Depends(get_current_user)):
    """
    Return protected prototype data for the executive business dashboard.

    This endpoint intentionally returns pre-shaped view-model data. In production,
    keep this style for fast dashboards by reading from cached/pre-aggregated
    analytics tables instead of calculating every KPI directly from transactions.
    """
    return {
        "metadata": {
            "authenticated_user": current_user["username"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dashboard_load_target_seconds": 3,
            "concurrent_employee_target": 200,
            "daily_order_capacity_target": 3000,
        },
        "summary": {
            "revenue": 1845000,
            "revenueTrend": "+12.8% vs last month",
            "ordersToday": 486,
            "pendingApprovals": 17,
            "riskAlerts": 4,
        },
        "bi": {
            "financialPerformance": [
                {"label": "Revenue", "value": 1845000, "max": 2200000},
                {"label": "Gross Profit", "value": 690000, "max": 2200000},
                {"label": "Operating Cost", "value": 410000, "max": 2200000},
                {"label": "Marketing Spend", "value": 120000, "max": 2200000},
            ],
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
        "reports": {
            "jobs": [
                {"name": "Revenue Summary - June", "status": "Ready"},
                {"name": "Marketing ROI export", "status": "Running"},
                {"name": "Cash Flow Forecast", "status": "Queued"},
            ],
        },
        "access": {
            "roles": [
                {
                    "role": "Executive",
                    "bi": "Yes",
                    "orders": "Yes",
                    "finance": "Yes",
                    "planning": "Yes",
                    "admin": "Limited",
                },
                {
                    "role": "Finance Manager",
                    "bi": "Yes",
                    "orders": "Limited",
                    "finance": "Yes",
                    "planning": "Yes",
                    "admin": "No",
                },
                {
                    "role": "Operations Staff",
                    "bi": "Limited",
                    "orders": "Yes",
                    "finance": "No",
                    "planning": "Limited",
                    "admin": "No",
                },
                {
                    "role": "Marketing Analyst",
                    "bi": "Yes",
                    "orders": "Limited",
                    "finance": "Limited",
                    "planning": "No",
                    "admin": "No",
                },
            ],
        },
        "marketing": {
            "funnel": [
                {"label": "Visitors", "value": 48500, "percent": 100},
                {"label": "Product Views", "value": 21800, "percent": 45},
                {"label": "Cart Adds", "value": 6200, "percent": 13},
                {"label": "Checkout Started", "value": 3600, "percent": 7},
                {"label": "Paid Orders", "value": 1480, "percent": 3},
            ],
            "channels": [
                {"label": "Paid Social", "roi": "3.8x", "spend": "₱48K"},
                {"label": "Email", "roi": "7.2x", "spend": "₱9K"},
                {"label": "Search", "roi": "4.4x", "spend": "₱31K"},
                {"label": "Referral", "roi": "5.1x", "spend": "₱12K"},
            ],
        },
    }
