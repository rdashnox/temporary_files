from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..schemas.shop import CheckoutRequest, CheckoutResponse, Product
from ..services import shop_service

router = APIRouter()


@router.get("/products", response_model=list[Product])
async def list_products(current_user: dict = Depends(get_current_user)):
    """Return protected product catalog data for the React dashboard."""
    return shop_service.list_products()


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    checkout_request: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate cart items, persist an order, and return a confirmation."""
    return shop_service.checkout(db, checkout_request, current_user)
