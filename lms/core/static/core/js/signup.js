window.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signupForm');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const password1Input = document.getElementById('password1');
    const password2Input = document.getElementById('password2');

    if (!signupForm || !usernameInput || !emailInput || !password1Input || !password2Input) {
        return;
    }

    signupForm.addEventListener('submit', (e) => {
        clearErrors();
        let hasError = false;

        if (!usernameInput.value.trim()) {
            showFieldError(usernameInput, 'Username is required.');
            hasError = true;
        }

        if (!emailInput.value.trim()) {
            showFieldError(emailInput, 'Email is required.');
            hasError = true;
        } else if (!isValidEmail(emailInput.value.trim())) {
            showFieldError(emailInput, 'Please enter a valid email address.');
            hasError = true;
        }

        if (!password1Input.value) {
            showFieldError(password1Input, 'Password is required.');
            hasError = true;
        } else if (password1Input.value.length < 8) {
            showFieldError(password1Input, 'Password must be at least 8 characters long.');
            hasError = true;
        }

        if (!password2Input.value) {
            showFieldError(password2Input, 'Please confirm your password.');
            hasError = true;
        } else if (password1Input.value !== password2Input.value) {
            showFieldError(password2Input, 'Passwords do not match.');
            hasError = true;
        }

        if (hasError) {
            e.preventDefault();
        }
    });

    [usernameInput, emailInput, password1Input, password2Input].forEach(input => {
        input.addEventListener('input', () => {
            clearFieldError(input);
        });
    });
});

function showFieldError(input, message) {
    const inputGroup = input.closest('.input-group');
    if (inputGroup) {
        let errorDiv = inputGroup.querySelector('.field-errors');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-errors';
            inputGroup.appendChild(errorDiv);
        }
        errorDiv.innerHTML = `<small class="error-text">${message}</small>`;
        input.classList.add('error');
    }
}

function clearErrors() {
    document.querySelectorAll('.input-group .field-errors').forEach(el => el.remove());
    document.querySelectorAll('.input-group input.error').forEach(el => el.classList.remove('error'));
}

function clearFieldError(input) {
    const inputGroup = input.closest('.input-group');
    if (inputGroup) {
        const errorDiv = inputGroup.querySelector('.field-errors');
        if (errorDiv) {
            errorDiv.remove();
        }
        input.classList.remove('error');
    }
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}