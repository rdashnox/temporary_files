from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .routes import auth
from .routes import data
from .routes import shop

app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend application (e.g., running on localhost:8080)
# to make requests to this backend API.
origins = settings.frontend_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
# Routes for authentication (login, registration)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# Routes for protected data
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
# Routes for product catalog, cart preview, and checkout
app.include_router(shop.router, prefix="/api/v1/shop", tags=["shop"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "message": "FastAPI backend is running"}


@app.get("/")
async def read_root():
    return {"message": "Welcome to FinMark Backend API", "health": "/api/v1/health"}
