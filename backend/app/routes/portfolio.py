from fastapi import APIRouter
from app.services.portfolio_service import get_portfolio_data

router = APIRouter()

@router.get("/")
def get_portfolio():
    return get_portfolio_data()