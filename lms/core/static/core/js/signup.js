document.getElementById('signupForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const fullname = document.getElementById('fullname').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validation
    if (!fullname) {
        showError('Please enter your full name');
        return;
    }

    if (!email) {
        showError('Please enter your email');
        return;
    }

    if (!isValidEmail(email)) {
        showError('Please enter a valid email address');
        return;
    }

    if (password.length < 6) {
        showError('Password must be at least 6 characters long');
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    // Success
    showSuccess(`Welcome ${fullname}! Your account has been created successfully.`);
    
    // Reset form
    document.getElementById('signupForm').reset();

    // Redirect after 2 seconds
    setTimeout(() => {
        window.location.href = 'login.html';
    }, 2000);
});

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showError(message) {
    const formBox = document.querySelector('.form-box');
    removeMessage();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message error';
    messageDiv.textContent = message;
    
    formBox.insertBefore(messageDiv, formBox.firstChild);

    setTimeout(() => {
        messageDiv.remove();
    }, 4000);
}

function showSuccess(message) {
    const formBox = document.querySelector('.form-box');
    removeMessage();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message success';
    messageDiv.textContent = message;
    
    formBox.insertBefore(messageDiv, formBox.firstChild);
}

function removeMessage() {
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
}
