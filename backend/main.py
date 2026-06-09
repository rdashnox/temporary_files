from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth
from .routes import data

app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend application (e.g., running on localhost:8080)
# to make requests to this backend API.
origins = [
    "http://localhost:8080",  # Frontend development server
    "http://127.0.0.1:8080",
    # Add other origins as needed for deployment or different frontend URLs
]

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

@app.get("/")
async def read_root():
    return {"message": "Welcome to FinMark Backend API"}
