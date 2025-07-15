from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import router as auth_router

app = FastAPI(
    title="Finance Tracker & Budgeting App API",
    description="REST API for finance tracker with user authentication, transactions, dashboard, analytics.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register authentication routes
app.include_router(auth_router)

@app.get("/", summary="Health Check", tags=["Misc"])
def health_check():
    """Basic health check endpoint to verify service is running."""
    return {"message": "Healthy"}
