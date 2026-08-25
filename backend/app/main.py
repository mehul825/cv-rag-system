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
    error_msg = None

    try:
        # Check PostgreSQL connection
        await db.execute(text("SELECT 1"))
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
        error_msg = str(e)

    status = (
        "healthy"
        if database_status == "healthy"
        else "degraded"
    )

    import urllib.parse
    db_host = "Unknown"
    db_port = "Unknown"
    db_name = "Unknown"
    try:
        # Clean scheme if needed
        url_to_parse = settings.DATABASE_URL
        if url_to_parse.startswith("postgresql+asyncpg://"):
            url_to_parse = url_to_parse.replace("postgresql+asyncpg://", "postgresql://", 1)
        parsed = urllib.parse.urlparse(url_to_parse)
        db_host = parsed.hostname or "Unknown"
        db_port = parsed.port or "Unknown"
        db_name = parsed.path.lstrip("/") if parsed.path else "Unknown"
    except Exception as parse_err:
        print(f"Error parsing database URL: {parse_err}")

    return {
        "status": status,
        "services": {
            "api": "healthy",
            "database": database_status
        },
        "diagnostics": {
            "db_host": db_host,
            "db_port": db_port,
            "db_name": db_name,
            "ssl_mode": "ssl=" in settings.DATABASE_URL or "sslmode=" in settings.DATABASE_URL,
            "running_in_docker": settings.RUNNING_IN_DOCKER,
            "error_detail": error_msg
        }
    }