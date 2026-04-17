from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.db.database import Base


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    shares = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    market_price = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    total_value = Column(Float, nullable=False, default=0)
    cash = Column(Float, nullable=False, default=0)
    daily_pnl = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)