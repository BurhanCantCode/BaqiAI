from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, users, transactions, demo, recommendations

app = FastAPI(
    title="BAQI AI",
    description="AI-Powered Investment Assistant for Pakistani Banking",
    version="0.1.0",
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
app.include_router(users.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
