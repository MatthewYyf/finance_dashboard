from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import portfolio
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])

@app.get("/")
def root():
    return {"message": "Finance Dashboard API is running"}