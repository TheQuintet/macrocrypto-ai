import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.websocket.btc_client import (
    connect_btc_price_stream
)


btc_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global btc_task

    btc_task = asyncio.create_task(
        connect_btc_price_stream()
    )

    yield

    btc_task.cancel()


app = FastAPI(
    title="MacroCrypto AI Backend",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "message": 
        "MacroCrypto AI Backend is running"
    }