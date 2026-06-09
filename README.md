# FinMark Login Prototype

This repository contains a functional prototype of a user login module for the FinMark project, developed as part of Milestone 2. It demonstrates a clean architecture with a Python FastAPI backend and a simple HTML/CSS/JavaScript frontend.

## Project Structure

```
.
├── backend/
│   ├── venv/                      # Python Virtual Environment
│   ├── main.py                    # Main FastAPI application
│   ├── routes/
│   │   └── auth.py                # Authentication routes (e.g., /token)
│   ├── controllers/
│   │   └── auth_controller.py     # Authentication logic orchestration
│   └── services/
│       └── auth_service.py        # Core authentication business logic (dummy)
└── frontend/
    ├── index.html                 # Main login page HTML
    ├── style.css                  # Styling for the login page
    └── script.js                  # Frontend JavaScript for form submission and API calls
```

## How to Run the Prototype

Follow these steps to get the FinMark Login Prototype running on your local machine.

### 1. Start the Backend

1.  **Navigate to the backend directory:**
    ```bash
    cd "C:\MMDC\Y3 T3\SUBJECTS\P-T\Milestone 2\Project Prototype\backend"
    ```
2.  **Activate the Python virtual environment:**
    ```bash
    .\venv\Scripts\activate
    ```
    *(If you haven't installed dependencies yet, run: `pip install fastapi uvicorn "python-multipart"`)*
3.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```
    This will start the backend server, typically accessible at `http://localhost:8000`. You should see output indicating that Uvicorn is running.

### 2. Open the Frontend

1.  **Navigate to the frontend directory:**
    ```bash
    cd "C:\MMDC\Y3 T3\SUBJECTS\P-T\Milestone 2\Project Prototype\frontend"
    ```
2.  **Open `index.html` in your web browser.**
    You can do this by simply double-clicking the `index.html` file in your file explorer, or by typing `start index.html` in the command line (on Windows).
    The login page should open in your default browser, typically at a URL like `file:///C:/MMDC/Y3 T3/SUBJECTS/P-T/Milestone 2/Project Prototype/frontend/index.html`.

### 3. Test the Login

Use the following dummy credentials for testing:

*   **Email:** `user@example.com`
*   **Password:** `password123`

1.  Enter these credentials into the login form.
2.  Click the "Login" button.
3.  You should see a "Login successful! Token: fake-jwt-token" message below the form. If login fails (e.g., incorrect credentials), an error message will be displayed.

## Key Design Decisions

*   **Clean Architecture:** Backend structured into routes, controllers, and services for clear separation of concerns, maintainability, and scalability.
*   **Python FastAPI Backend:** Chosen for its high performance, ease of use, and alignment with the project's architectural discussions.
*   **HTML/CSS/JS Frontend:** A simple, direct approach for the frontend to quickly demonstrate functionality without the overhead of a full frontend framework, while using essential web technologies.
*   **CORS Enabled:** The FastAPI backend is configured to allow requests from the frontend running locally, preventing common cross-origin issues.
*   **Dummy Authentication:** Credentials are hardcoded in the `auth_service.py` for demonstration purposes. In a real application, this would interact with a database and securely hash passwords.
*   **Fake JWT Token:** A placeholder token is returned to simulate successful authentication and session management.

## Next Steps

This prototype provides a foundational login module. Future enhancements would include:

*   Database integration for user management.
*   Proper JWT generation, validation, and session handling.
*   User registration and password reset functionality.
*   Integration with the broader FinMark dashboard and services.
*   Robust error handling and input validation.
*   Deployment to a containerized environment (e.g., Docker, Kubernetes).
