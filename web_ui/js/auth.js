/**
 * Authentication logic for AI Culinary Expert
 * Handles login, registration, and session management
 */

const API_BASE = '/api';

/**
 * Show error message in form
 */
function showError(formId, message) {
    const errorDiv = document.getElementById(`${formId}-error`);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

/**
 * Hide error message
 */
function hideError(formId) {
    const errorDiv = document.getElementById(`${formId}-error`);
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());

    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * Switch between login and register tabs
 */
function switchTab(tab) {
    // Update tab buttons
    document.getElementById('login-tab').classList.toggle('active', tab === 'login');
    document.getElementById('register-tab').classList.toggle('active', tab === 'register');

    // Show/hide forms
    document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';

    // Clear errors
    hideError('login');
    hideError('register');
}

/**
 * Handle login form submission
 */
async function handleLogin(event) {
    event.preventDefault();
    hideError('login');

    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        if (data.success) {
            // Store user in localStorage
            localStorage.setItem('user', JSON.stringify(data.user));
            showToast('Login successful!', 'success');
            
            // Redirect to home
            setTimeout(() => {
                window.location.href = 'home.html';
            }, 500);
        } else {
            throw new Error('Login failed');
        }
    } catch (error) {
        showError('login', error.message || 'Login failed. Please try again.');
    }
}

/**
 * Handle registration form submission
 */
async function handleRegister(event) {
    event.preventDefault();
    hideError('register');

    const formData = new FormData(event.target);
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');

    // Client-side validation
    if (password !== confirmPassword) {
        showError('register', 'Passwords do not match');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        if (data.success) {
            // Store user in localStorage
            localStorage.setItem('user', JSON.stringify(data.user));
            showToast('Account created successfully!', 'success');
            
            // Redirect to home
            setTimeout(() => {
                window.location.href = 'home.html';
            }, 500);
        } else {
            throw new Error('Registration failed');
        }
    } catch (error) {
        showError('register', error.message || 'Registration failed. Please try again.');
    }
}

// Initialize login form if on login page
if (document.getElementById('login-form-element')) {
    document.getElementById('login-form-element').addEventListener('submit', handleLogin);
}

// Initialize register form if on register page
if (document.getElementById('register-form-element')) {
    document.getElementById('register-form-element').addEventListener('submit', handleRegister);
}
