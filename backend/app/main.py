from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import Base, engine

from app.api.routers import (
    users,
    roles,
    dashboard,
    customers,
    sales,
    analytics,
)

from app.api.routers.ai import (
    router as ai_router,
)

from app.api.routers.forecast import (
    router as forecast_router,
)

from app.api.routers.alerts import (
    router as alerts_router,
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="Enterprise AI Business Copilot",
    description=(
        "AI-Powered Business Analytics, "
        "Decision Support, Sales Forecasting "
        "and Business Risk Detection Platform"
    ),
    version="1.0.0",
)


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    users.router
)

app.include_router(
    roles.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    customers.router
)

app.include_router(
    sales.router
)

app.include_router(
    analytics.router
)

app.include_router(
    ai_router
)

app.include_router(
    forecast_router
)

app.include_router(
    alerts_router
)


@app.get("/")
def root():
    return {
        "message": "Enterprise AI Business Copilot API",
        "status": "running",
        "backend": "FastAPI",
        "database": "MySQL",
        "modules": [
            "Authentication",
            "Dashboard",
            "Customers",
            "Sales",
            "Analytics",
            "AI Copilot",
            "Sales Forecast",
            "Machine Learning",
            "AI Business Alerts",
            "Business Risk Detection",
        ],
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Backend is running successfully",
    }