from pydantic import BaseModel

class Position(BaseModel):
    symbol: str
    shares: float
    avg_cost: float