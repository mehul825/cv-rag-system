from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db, Base, engine
from app.models.resume import Resume, ResumeChunk
from app.api.cv import router as cv_router


# Reference models to register them with Base.metadata
_ = [Resume, ResumeChunk]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize database tables and columns when the application starts.
    """

    try:
        async with engine.begin() as conn:
            # Create database tables
            await conn.run_sync(Base.metadata.create_all)

            # Add required columns if they do not already exist
            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS extracted_json JSON;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS extracted_data JSON;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS status "
                    "VARCHAR DEFAULT 'queued';"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS error_message TEXT;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS trace_id VARCHAR;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS parsing_duration FLOAT;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS extraction_duration FLOAT;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS indexing_duration FLOAT;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS verification_duration FLOAT;"
                )
            )

            await conn.execute(
                text(
                    "ALTER TABLE resumes "
                    "ADD COLUMN IF NOT EXISTS total_duration FLOAT;"
                )
            )

        print("Database tables initialized successfully.")

    except Exception as e:
        print(
            "Warning: Database initialization failed "
            f"(local db may be offline): {e}"
        )

    yield

    print("Application shutting down.")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Powered CV Parsing, RAG & 5-Second Readiness Pipeline",
    version="1.0.0",
    lifespan=lifespan,
)


# CORS Middleware
# Allow Vercel frontend and local development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Register API routes
app.include_router(cv_router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CV RAG System API is running",
        "status": "healthy"
    }


# Health check endpoint
@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    database_status = "healthy"

    try:
        # Check PostgreSQL connection
        await db.execute(text("SELECT 1"))

    except Exception as e:
        if not settings.RUNNING_IN_DOCKER:
            database_status = "healthy (mocked locally)"
        else:
            database_status = f"unhealthy: {str(e)}"

    status = (
        "healthy"
        if database_status.startswith("healthy")
        else "degraded"
    )

    return {
        "status": status,
        "services": {
            "api": "healthy",
            "database": database_status
        }
    }