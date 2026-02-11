from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, users, transactions, demo, recommendations, investments, portfolio, telegram, upload, insights
from app.services.telegram_bot import start_bot, stop_bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start Telegram bot on startup, stop on shutdown."""
    await start_bot()
    yield
    await stop_bot()


app = FastAPI(
    title="BAQI AI",
    description="AI-Powered Investment Assistant for Pakistani Banking",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(investments.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(telegram.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
