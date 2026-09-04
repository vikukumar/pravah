import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import PravahException

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure local upload directories exist
    upload_dir = Path(settings.STORAGE_LOCAL_PATH)
    upload_dir.mkdir(parents=True, exist_ok=True)
    generated_dir = upload_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    # Automatically create tables for SQLite/dev mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PRAVAH - AI Social Media Management & Automation Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development allow all; in production configured via settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Central Exception Handler for Structured Errors
@app.exception_handler(PravahException)
async def pravah_exception_handler(request: Request, exc: PravahException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.detail,
            "meta": exc.meta,
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )

# Health & Version Probes
@app.get("/health", tags=["Observability"])
async def health_check():
    from app.core.version import get_version_info
    v_info = get_version_info()
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": v_info["backend_version"],
        "api_version": settings.API_V1_STR,
        "schema_version": v_info.get("schema_version"),
        "environment": settings.ENVIRONMENT,
    }

@app.get("/version", tags=["Observability"])
@app.get(f"{settings.API_V1_STR}/version", tags=["Observability"])
async def version_endpoint():
    from app.core.version import get_version_info
    return get_version_info()

@app.get("/ready", tags=["Observability"])
async def readiness_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)},
        )

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount local media uploads
_upload_path = Path(settings.STORAGE_LOCAL_PATH)
_upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_upload_path)), name="uploads")
app.mount("/api/v1/media", StaticFiles(directory=str(_upload_path)), name="media")
