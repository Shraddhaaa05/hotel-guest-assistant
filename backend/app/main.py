"""
FastAPI application entrypoint.

Mounts the health, chat, and availability routers, configures CORS for
local frontend development, and installs a global exception handler so
unhandled errors return a clean structured JSON response instead of a
raw stack trace.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import availability, chat, health
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="Grand Horizon Hotel - Guest Assistant API",
    description="Backend API for the AI-powered hotel guest assistant.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(availability.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convert Pydantic validation errors into a clean, consistent error
    shape instead of FastAPI's default verbose format.
    """
    logger.warning("request_validation_failed path=%s errors=%s", request.url.path, exc.errors())
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(p) for p in first_error.get("loc", []) if p != "body")
    message = first_error.get("msg", "Invalid request.")
    return JSONResponse(
        status_code=422,
        content={
            "message": f"Invalid request: {message}" + (f" (field: {field})" if field else ""),
            "type": "error",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last-resort safety net: never leak a raw 500/stack trace to the client."""
    logger.error("unhandled_exception path=%s error=%s", request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "message": "Something went wrong on our end. Please try again.",
            "type": "error",
        },
    )
