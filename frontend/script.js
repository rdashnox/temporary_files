/*
    Assigned to: Almer
    Task: Frontend Task 3 - Client-Side Form Validation & Feedback

    Description:
    Implement robust client-side validation for the login form BEFORE sending data to the backend.
    Provide immediate and clear feedback to the user regarding validation errors.

    Deliverables:
    1.  Modify this 'script.js' file to add comprehensive validation logic to the 'loginForm' submit event.
    2.  Validation rules:
        -   'username' (email) field must not be empty.
        -   'username' (email) field must be a valid email format (use a robust regular expression).
        -   'password' field must not be empty.
        -   'password' field should meet a minimum length requirement (e.g., 8 characters for a strong password).
    3.  If validation fails, prevent form submission to the backend.
    4.  Display clear and user-friendly validation error messages prominently. For instance, show errors
        next to the input fields or use the 'messageElement' effectively.
        Use appropriate styling (e.g., red text for errors) for these messages.
    5.  Ensure that all client-side validation error messages are cleared when the user starts typing again
        in the respective field or on a new submission attempt.

    Considerations:
    -   You can leverage HTML5 form validation attributes (e.g., 'required', 'type="email"') but enhance them
        with custom JavaScript for a better user experience.
    -   The 'messageElement' already exists for displaying server-side feedback; extend its use for client-side
        validation feedback.
    -   Do NOT modify the existing backend fetch logic; all validation should occur prior to it.
*/
/*
    Assigned to: Conrado
    Task: Frontend Task 4 - Post-Login Redirection & Token Storage

    Description:
    Implement redirection logic in this script so that upon successful login, the user is navigated
    to the 'dashboard.html' page. Additionally, securely store the received access token.

    Deliverables:
    1.  Modify the 'if (response.ok)' block below to redirect the user to 'dashboard.html'
        after successfully receiving a token.
    2.  Store the received 'data.access_token' in `localStorage` (e.g., `localStorage.setItem('access_token', data.access_token);`)
        so it can be retrieved by other frontend parts (like a dashboard page to access protected routes).
    3.  (Optional): If you have time, also store the username to display on the dashboard (e.g., parse from token if structured).

    Considerations:
    -   Use `window.location.href = 'dashboard.html';` for redirection.
    -   Ensure the token is stored correctly for future use.
    -   Coordinate with Aleczandra (Backend Task 3) who will be structuring the token.
*/
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const messageElement = document.getElementById('message');

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // Clear previous messages
        messageElement.textContent = '';
        messageElement.className = 'message';

        // --- Start of Almer's Frontend Task 3: Client-Side Validation ---
        let isValid = true;
        // Example: Check if username is empty
        if (!username.trim()) {
            messageElement.textContent = 'Email cannot be empty.';
            messageElement.classList.add('error');
            isValid = false;
        } else if (!/\S+@\S+\.\S+/.test(username)) { // Basic email regex check
            messageElement.textContent = 'Please enter a valid email address.';
            messageElement.classList.add('error');
            isValid = false;
        }

        if (!password.trim()) {
            // If another error already exists, append; otherwise, set new message
            messageElement.textContent += (isValid ? '' : ' ') + 'Password cannot be empty.';
            messageElement.classList.add('error');
            isValid = false;
        }
        // Example: Password length check
        if (password.length < 8) {
             messageElement.textContent += (isValid ? '' : ' ') + 'Password must be at least 8 characters long.';
             messageElement.classList.add('error');
             isValid = false;
        }


        if (!isValid) {
            return; // Stop if client-side validation fails
        }
        // --- End of Almer's Frontend Task 3 ---


        // Create form data as per OAuth2PasswordRequestForm expected by FastAPI
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch('http://localhost:8000/api/v1/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const data = await response.json();

            if (response.ok) {
                // --- Start of Conrado's Frontend Task 4: Redirection and Token Storage ---
                localStorage.setItem('access_token', data.access_token); // Store token
                window.location.href = 'dashboard.html'; // Redirect to dashboard
                // --- End of Conrado's Frontend Task 4 ---
            } else {
                messageElement.textContent = `Login failed: ${data.detail}`;
                messageElement.classList.add('error');
                console.error('Login failed:', data);
            }
        } catch (error) {
            messageElement.textContent = 'An error occurred during login. Please try again later.';
            messageElement.classList.add('error');
            console.error('Network or unexpected error:', error);
        }
    });
});