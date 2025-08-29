/**
 * Authentication JavaScript for Food Premi
 * Handles login, signup, form validation, and user interactions
 */

// API Base URL
const API_BASE = 'http://localhost:5000/api';
// Expose base URL for other scripts
window.API_BASE = API_BASE;

// DOM Elements
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const alertMessage = document.getElementById('alertMessage');

// Initialize authentication
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});

function initializeAuth() {
    // Check authentication status
    checkAuthStatus();
    
    // Initialize form handlers
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
        initializePasswordStrength();
        initializeFormValidation();
    }
    
    // Initialize alert close button
    const alertClose = document.querySelector('.alert-close');
    if (alertClose) {
        alertClose.addEventListener('click', hideAlert);
    }
    
    // Auto-hide alerts after 5 seconds
    setTimeout(hideAlert, 5000);
}

// Password visibility toggle
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const toggleBtn = field.nextElementSibling.querySelector('i');
    const toggleWrapper = field.nextElementSibling;
    
    if (field.type === 'password') {
        field.type = 'text';
        toggleBtn.classList.remove('fa-eye');
        toggleBtn.classList.add('fa-eye-slash');
        if (toggleWrapper) toggleWrapper.setAttribute('aria-label', 'Hide password');
    } else {
        field.type = 'password';
        toggleBtn.classList.remove('fa-eye-slash');
        toggleBtn.classList.add('fa-eye');
        if (toggleWrapper) toggleWrapper.setAttribute('aria-label', 'Show password');
    }
}

// Password strength checker
function initializePasswordStrength() {
    const passwordField = document.getElementById('password');
    const strengthBar = document.querySelector('.strength-fill');
    const strengthText = document.querySelector('.strength-text');
    
    if (passwordField && strengthBar && strengthText) {
        passwordField.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            updatePasswordStrength(strength, strengthBar, strengthText);
        });
    }
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    if (password.length >= 8) score += 1;
    if (password.match(/[a-z]/)) score += 1;
    if (password.match(/[A-Z]/)) score += 1;
    if (password.match(/[0-9]/)) score += 1;
    if (password.match(/[^A-Za-z0-9]/)) score += 1;
    
    return score;
}

function updatePasswordStrength(score, strengthBar, strengthText) {
    // Remove existing classes
    strengthBar.className = 'strength-fill';
    
    if (score === 0) {
        strengthText.textContent = 'Enter a password';
        strengthBar.style.width = '0%';
    } else if (score <= 2) {
        strengthBar.classList.add('weak');
        strengthText.textContent = 'Weak password';
    } else if (score === 3) {
        strengthBar.classList.add('fair');
        strengthText.textContent = 'Fair password';
    } else if (score === 4) {
        strengthBar.classList.add('good');
        strengthText.textContent = 'Good password';
    } else {
        strengthBar.classList.add('strong');
        strengthText.textContent = 'Strong password';
    }
}

// Form validation
function initializeFormValidation() {
    const confirmPasswordField = document.getElementById('confirmPassword');
    const passwordField = document.getElementById('password');
    
    if (confirmPasswordField && passwordField) {
        confirmPasswordField.addEventListener('input', function() {
            validatePasswordMatch(passwordField.value, this.value);
        });
        
        passwordField.addEventListener('input', function() {
            if (confirmPasswordField.value) {
                validatePasswordMatch(this.value, confirmPasswordField.value);
            }
        });
    }
    
    // Phone number validation
    const phoneField = document.getElementById('phone');
    if (phoneField) {
        phoneField.addEventListener('input', function() {
            validatePhoneNumber(this.value);
        });
    }
    
    // Email validation
    const emailField = document.getElementById('email');
    if (emailField) {
        emailField.addEventListener('input', function() {
            validateEmail(this.value);
        });
    }
}

function validatePasswordMatch(password, confirmPassword) {
    const confirmField = document.getElementById('confirmPassword');
    
    if (confirmPassword && password !== confirmPassword) {
        confirmField.setCustomValidity('Passwords do not match');
        confirmField.style.borderColor = 'var(--error-color)';
    } else {
        confirmField.setCustomValidity('');
        confirmField.style.borderColor = password && confirmPassword ? 'var(--success-color)' : '';
    }
}

function validatePhoneNumber(phone) {
    const phoneField = document.getElementById('phone');
    const indianPhoneRegex = /^[6-9]\d{9}$/;
    
    if (phone && !indianPhoneRegex.test(phone)) {
        phoneField.setCustomValidity('Please enter a valid 10-digit phone number');
        phoneField.style.borderColor = 'var(--error-color)';
    } else {
        phoneField.setCustomValidity('');
        phoneField.style.borderColor = phone ? 'var(--success-color)' : '';
    }
}

function validateEmail(email) {
    const emailField = document.getElementById('email');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        emailField.setCustomValidity('Please enter a valid email address');
        emailField.style.borderColor = 'var(--error-color)';
    } else {
        emailField.setCustomValidity('');
        emailField.style.borderColor = email ? 'var(--success-color)' : '';
    }
}

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('loginBtn');
    const formData = new FormData(loginForm);
    
    // Show loading state
    setButtonLoading(submitBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: formData.get('email'),
                password: formData.get('password')
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'Login successful! Redirecting...', 'fas fa-check-circle');
            
            // Store user info in localStorage
            localStorage.setItem('user', JSON.stringify(result.user));
            localStorage.setItem('isLoggedIn', 'true');
            
            // Redirect to main page after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            showAlert('error', result.message || 'Login failed. Please try again.', 'fas fa-exclamation-circle');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('error', 'Network error. Please check your connection and try again.', 'fas fa-exclamation-triangle');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// Handle signup form submission
async function handleSignup(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('signupBtn');
    const formData = new FormData(signupForm);
    
    // Validate password match
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    if (password !== confirmPassword) {
        showAlert('error', 'Passwords do not match!', 'fas fa-exclamation-circle');
        return;
    }
    
    // Validate terms agreement
    const agreeTerms = document.getElementById('agreeTerms').checked;
    if (!agreeTerms) {
        showAlert('error', 'Please agree to the Terms & Conditions to continue.', 'fas fa-exclamation-circle');
        return;
    }
    
    // Show loading state
    setButtonLoading(submitBtn, true);
    
    try {
        const userData = {
            name: formData.get('name'),
            email: formData.get('email'),
            phone: formData.get('phone'),
            password: formData.get('password'),
            address: formData.get('address') || ''
        };
        
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'Account created successfully! Please login to continue.', 'fas fa-check-circle');
            
            // Redirect to login page after short delay
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            showAlert('error', result.message || 'Registration failed. Please try again.', 'fas fa-exclamation-circle');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showAlert('error', 'Network error. Please check your connection and try again.', 'fas fa-exclamation-triangle');
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth-status`);
        const result = await response.json();
        
        if (result.logged_in) {
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('userId', result.user_id);
            localStorage.setItem('userName', result.user_name);
        } else {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userId');
            localStorage.removeItem('userName');
            localStorage.removeItem('user');
        }
    } catch (error) {
        console.error('Auth status check failed:', error);
    }
}

// Logout function
async function logout() {
    try {
        const response = await fetch(`${API_BASE}/logout`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear local storage
            localStorage.clear();
            
            showAlert('success', 'Logged out successfully!', 'fas fa-check-circle');
            
            // Redirect to home page
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        }
    } catch (error) {
        console.error('Logout error:', error);
        showAlert('error', 'Logout failed. Please try again.', 'fas fa-exclamation-circle');
    }
}

// Utility functions
function setButtonLoading(button, loading) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

function showAlert(type, message, icon) {
    if (!alertMessage) return;
    
    const alertIcon = alertMessage.querySelector('.alert-icon');
    const alertText = alertMessage.querySelector('.alert-text');
    
    // Set alert type class
    alertMessage.className = `alert-message ${type}`;
    
    // Set icon and message
    alertIcon.className = `alert-icon ${icon}`;
    alertText.textContent = message;
    
    // Show alert
    alertMessage.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(hideAlert, 5000);
}

function hideAlert() {
    if (alertMessage) {
        alertMessage.classList.remove('show');
    }
}

// Social login handlers (placeholder)
document.addEventListener('click', function(e) {
    if (e.target.closest('.social-btn.google')) {
        showAlert('warning', 'Google login will be available soon!', 'fab fa-google');
    }
});

// Export functions for use in other scripts
window.authUtils = {
    logout,
    checkAuthStatus,
    showAlert
};