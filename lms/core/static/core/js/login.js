window.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const rememberCheckbox = document.getElementById('remember');

    if (!loginForm || !usernameInput || !passwordInput || !rememberCheckbox) {
        return;
    }

    const rememberedUsername = localStorage.getItem('rememberUsername');
    if (rememberedUsername) {
        usernameInput.value = rememberedUsername;
        rememberCheckbox.checked = true;
    }

    loginForm.addEventListener('submit', (e) => {
        clearErrors();
        let hasError = false;

        if (!usernameInput.value.trim()) {
            showFieldError(usernameInput, 'Username is required.');
            hasError = true;
        }

        if (!passwordInput.value) {
            showFieldError(passwordInput, 'Password is required.');
            hasError = true;
        }

        if (hasError) {
            e.preventDefault();
            return;
        }

        if (rememberCheckbox.checked && usernameInput.value.trim()) {
            localStorage.setItem('rememberUsername', usernameInput.value.trim());
        } else {
            localStorage.removeItem('rememberUsername');
        }
    });

    [usernameInput, passwordInput].forEach(input => {
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