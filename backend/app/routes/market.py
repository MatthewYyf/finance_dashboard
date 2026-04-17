from fastapi import APIRouter

router = APIRouter()

@router.get("/overview")
def market_overview():
    return [
        {"symbol": "SPY", "price": 523.14, "change": 0.82},
        {"symbol": "QQQ", "price": 447.52, "change": -0.41},
        {"symbol": "AAPL", "price": 198.27, "change": 1.15},
    ]