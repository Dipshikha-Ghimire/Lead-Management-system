window.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const rememberCheckbox = document.getElementById('remember');

    if (!loginForm || !usernameInput || !rememberCheckbox) {
        return;
    }

    const rememberedUsername = localStorage.getItem('rememberUsername');
    if (rememberedUsername) {
        usernameInput.value = rememberedUsername;
        rememberCheckbox.checked = true;
    }

    loginForm.addEventListener('submit', () => {
        const username = usernameInput.value.trim();

        if (rememberCheckbox.checked && username) {
            localStorage.setItem('rememberUsername', username);
        } else {
            localStorage.removeItem('rememberUsername');
        }
    });
});
