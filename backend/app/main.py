"""FastAPI main application entrypoint for MuleNet."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import API_VERSION, CORS_ORIGINS
from backend.app.errors import (
    APIError,
    INTERNAL_ERROR,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    NOT_IMPLEMENTED,
    VALIDATION_ERROR,
)
from backend.app.routes import accounts, alerts, curve, drift, health, summary

app = FastAPI(
    title="MuleNet API",
    version=API_VERSION,
    description="API for detecting fraud networks (mule accounts) in UPI-style transactions",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom APIError exceptions with standardized error envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors with 422 VALIDATION_ERROR envelope."""
    errors_list = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors_list.append({"field": field, "message": err.get("msg", "")})

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": VALIDATION_ERROR,
                "message": "Validation error in request parameters",
                "details": {"errors": errors_list},
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette / FastAPI HTTPExceptions with standard error envelope."""
    if exc.status_code == 404:
        code = NOT_FOUND
        msg = "Resource not found"
    elif exc.status_code == 405:
        code = METHOD_NOT_ALLOWED
        msg = "Method not allowed"
    else:
        code = "HTTP_ERROR"
        msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": msg,
                "details": {},
            }
        },
    )


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(
    request: Request, exc: NotImplementedError
) -> JSONResponse:
    """Handle NotImplementedError with 501 NOT_IMPLEMENTED envelope."""
    return JSONResponse(
        status_code=501,
        content={
            "error": {
                "code": NOT_IMPLEMENTED,
                "message": str(exc) or "Endpoint not implemented",
                "details": {},
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle generic unexpected exceptions with 500 INTERNAL_ERROR envelope."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": INTERNAL_ERROR,
                "message": "An internal server error occurred.",
                "details": {},
            }
        },
    )


# Include Routers with /api prefix
app.include_router(health.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(curve.router, prefix="/api")
app.include_router(drift.router, prefix="/api")
