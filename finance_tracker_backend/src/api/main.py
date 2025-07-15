from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .auth import router as auth_router
from .transactions import router as transactions_router
from .db import init_db

# PUBLIC_INTERFACE
def create_app():
    """
    Create and configure the FastAPI app with CORS and robust error handlers.
    Returns:
        FastAPI: The configured FastAPI app.
    """
    app = FastAPI(
        title="Finance Tracker & Budgeting App API",
        description="REST API for finance tracker with user authentication, transactions, dashboard, analytics.",
        version="1.0.0"
    )

    # CORS - allow all for local development, restrict for prod
    # CORS - comprehensive setup for Flutter/web (local dev + mobile emulator + cloud preview)
    # Add more origins here if needed (e.g., real prod, preview URLs)
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:3000",           # Android emulator
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        # Allow Kavia Cloud Preview and any additional dynamic cloud origins
        "https://vscode-internal-4816-beta.beta01.cloud.kavia.ai:3001",
        # Optionally support everything during early dev (remove * for production security)
        # "*",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],  # Expose all headers so the frontend can read tokens if provided
        max_age=600,
    )

    # Init DB on startup (if required)
    @app.on_event("startup")
    def on_startup():
        init_db()

    # Centralized error handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors in a consistent JSON format."""
        return JSONResponse(
            status_code=404,
            content={"error": "Resource not found", "detail": str(exc)},
        )

    @app.exception_handler(422)
    async def validation_exception_handler(request: Request, exc):
        """Handle request validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "detail": exc.errors() if hasattr(exc, 'errors') else str(exc)
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc):
        """Handle any uncaught exceptions with JSON error."""
        return JSONResponse(
            status_code=500,
            content={"error": "Server error", "detail": str(exc)},
        )

    # Register authentication and transaction routes
    app.include_router(auth_router)
    app.include_router(transactions_router)

    # Health check endpoint
    @app.get("/", summary="Health Check", tags=["Misc"])
    def health_check():
        """Basic health check endpoint to verify service is running."""
        return {"message": "Healthy"}

    return app

app = create_app()
