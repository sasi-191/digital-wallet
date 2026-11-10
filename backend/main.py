from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import auth_routes, wallet_routes


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)     # make the tables if they do not exist
    yield


app = FastAPI(title="Digital Wallet and Payments Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(wallet_routes.router)


@app.get("/")
def home():
    return {"message": "Digital Wallet is running. Open /docs to see the API."}
