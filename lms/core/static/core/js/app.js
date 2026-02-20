// Toggle between signup and login forms
function toggleForms() {
    const signupForm = document.querySelector('.signup-form');
    const loginForm = document.querySelector('.login-form');

    signupForm.classList.toggle('active');
    loginForm.classList.toggle('active');
}

// Form submission handlers
document.addEventListener('DOMContentLoaded', () => {
    const signupFormElement = document.querySelector('.signup-form form');
    const loginFormElement = document.querySelector('.login-form form');

    signupFormElement.addEventListener('submit', (e) => {
        e.preventDefault();
        const fullName = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;

        // Simple validation
        if (password !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }

        if (fullName && email && password) {
            alert(`Account created successfully for ${fullName}!`);
            signupFormElement.reset();
        }
    });

    loginFormElement.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const rememberMe = document.getElementById('remember-me').checked;

        if (email && password) {
            alert(`Login successful for ${email}!`);
            if (rememberMe) {
                alert('Remember me option enabled');
            }
            loginFormElement.reset();
        }
    });
});
