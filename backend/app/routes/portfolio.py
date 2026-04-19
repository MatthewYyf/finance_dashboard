from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.portfolio_service import (
    get_saved_portfolio,
    get_live_portfolio,
    refresh_portfolio,
)

router = APIRouter()


@router.get("/")
def get_portfolio(db: Session = Depends(get_db)):
    return get_saved_portfolio(db)


@router.get("/live")
def get_portfolio_live(db: Session = Depends(get_db)):
    return get_live_portfolio(db)


@router.post("/refresh")
def refresh_portfolio_route(db: Session = Depends(get_db)):
    return refresh_portfolio(db)