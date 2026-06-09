from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth
from .routes import data # Import the new data router

#
# Assigned to: Almer
# Task: Backend Task 5 - Integrate Protected Endpoint & Main App Configuration
#
# Description:
# This task ensures that the new protected data endpoint is correctly integrated into the main FastAPI application.
# It also includes a review of the CORS configuration for compatibility.
#
# Deliverables:
# 1.  Ensure that the `data.router` (defined in `backend/routes/data.py`) is correctly included
#     in this `main.py` file using `app.include_router()`. This has already been added as a placeholder.
# 2.  Verify the CORS (Cross-Origin Resource Sharing) configuration is correct and allows the frontend
#     (running on http://localhost:8080 or http://127.0.0.1:8080) to communicate with the backend.
#     Adjust `origins` if necessary based on how the frontend will be served.
#
# Considerations:
# - The `prefix` and `tags` for the data router should be consistent with API versioning and documentation.
# - If the frontend will eventually be hosted on a different URL, that URL must be added to the `origins` list.
#
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:8080",  # Frontend development server
    "http://127.0.0.1:8080",
    # Add other origins as needed for deployment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"]) # Include the new data router

@app.get("/")
async def read_root():
    return {"message": "Welcome to FinMark Backend API"}