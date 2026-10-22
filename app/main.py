import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.seed.seed_data import seed_database
from app.core.scheduler import start_scheduler, stop_scheduler

from app.routers.auth import router as auth_router
from app.routers.subjects import router as subjects_router
from app.routers.questions import router as questions_router
from app.routers.quiz import router as quiz_router
from app.routers.resources import router as resources_router
from app.routers.reminders import router as reminders_router
from app.routers.analytics import router as analytics_router
from app.routers.admin import router as admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist & seed minimal baseline data
    Base.metadata.create_all(bind=engine)
    try:
        seed_database()
    except Exception as e:
        print(f"Seed note: {e}")

    # Start background scheduler for reminders
    start_scheduler()
    yield
    # Shutdown: Stop scheduler cleanly
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade Backend REST API for MBA Semester 1 Study Hub. Covers authentication, 8 subjects, verified syllabus units, 30-mark quiz generation (10/10/10), exam scoring, resources library, and analytics.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
api_v1_prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(subjects_router, prefix=api_v1_prefix)
app.include_router(questions_router, prefix=api_v1_prefix)
app.include_router(quiz_router, prefix=api_v1_prefix)
app.include_router(resources_router, prefix=api_v1_prefix)
app.include_router(reminders_router, prefix=api_v1_prefix)
app.include_router(analytics_router, prefix=api_v1_prefix)
app.include_router(admin_router, prefix=api_v1_prefix)

@app.get("/", tags=["Health"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/docs",
        "api_v1": settings.API_V1_PREFIX
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "up",
        "environment": settings.ENV,
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
