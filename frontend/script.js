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

        // Implement client-side form validation here.
        // Check for empty fields, valid email format, and password strength.
        // If validation fails, display error messages and return early.
        let isValid = true;
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
            messageElement.textContent += (isValid ? '' : ' ') + 'Password cannot be empty.';
            messageElement.classList.add('error');
            isValid = false;
        }
        if (password.length < 8) {
             messageElement.textContent += (isValid ? '' : ' ') + 'Password must be at least 8 characters long.';
             messageElement.classList.add('error');
             isValid = false;
        }
        if (!isValid) {
            return;
        }

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
                // On successful login, store the access token and redirect to the dashboard.
                localStorage.setItem('access_token', data.access_token);
                window.location.href = 'dashboard.html';
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
