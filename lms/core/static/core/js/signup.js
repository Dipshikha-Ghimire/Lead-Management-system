window.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signupForm');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const password1Input = document.getElementById('password1');
    const password2Input = document.getElementById('password2');

    if (!signupForm || !usernameInput || !emailInput || !password1Input || !password2Input) {
        return;
    }

    signupForm.addEventListener('submit', (event) => {
        clearClientError();

        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password1 = password1Input.value;
        const password2 = password2Input.value;

        if (!username) {
            event.preventDefault();
            showClientError('Please enter your username.');
            return;
        }

        if (!email) {
            event.preventDefault();
            showClientError('Please enter your email address.');
            return;
        }

        if (password1.length < 8) {
            event.preventDefault();
            showClientError('Password must be at least 8 characters long.');
            return;
        }

        if (password1 !== password2) {
            event.preventDefault();
            showClientError('Passwords do not match.');
        }
    });
});

function showClientError(message) {
    const form = document.getElementById('signupForm');
    const errorBlock = document.createElement('div');
    errorBlock.className = 'field-errors client-error';
    errorBlock.innerHTML = `<small class="error-text">${message}</small>`;
    form.insertBefore(errorBlock, form.querySelector('.btn-submit'));
}

function clearClientError() {
    const existing = document.querySelector('.client-error');
    if (existing) {
        existing.remove();
    }
}
