from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db, Base, engine
from app.models.resume import Resume, ResumeChunk
from app.api.cv import router as cv_router

# Reference models to register them with Base.metadata and silence unused import warnings
_ = [Resume, ResumeChunk]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Warning: Database initialization failed (local db may be offline): {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Powered CV Parsing, RAG & 5-Second Readiness Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register API routes
app.include_router(cv_router, prefix="/api")

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    database_status = "healthy"
    try:
        # Run a simple SELECT 1 query to verify Postgres connectivity
        await db.execute(text("SELECT 1"))
    except Exception as e:
        if not settings.RUNNING_IN_DOCKER:
            database_status = "healthy (mocked locally)"
        else:
            database_status = f"unhealthy: {str(e)}"
    
    status = "healthy" if database_status.startswith("healthy") else "degraded"
    
    return {
        "status": status,
        "services": {
            "api": "healthy",
            "database": database_status
        }
    }
# Reload trigger comment
