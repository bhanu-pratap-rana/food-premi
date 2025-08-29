/**
 * Navigation Authentication Handler for Food Premi
 * Manages the display of login/logout links in navigation
 */

document.addEventListener('DOMContentLoaded', function() {
    updateAuthNavigation();
});

function updateAuthNavigation() {
    const authLinksContainer = document.getElementById('authLinks');
    if (!authLinksContainer) return;
    
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const userName = localStorage.getItem('userName');
    const userJson = localStorage.getItem('user');
    const user = userJson ? JSON.parse(userJson) : null;
    
    if (isLoggedIn && userName) {
        // User is logged in - show welcome message and logout button
        authLinksContainer.innerHTML = `
            <div class="profile-menu">
                <button class="profile-trigger" aria-haspopup="true" aria-expanded="false">
                    <img class="profile-avatar" src="${(user && user.avatar) || 'https://i.pravatar.cc/60'}" alt="Profile"/>
                    <span class="profile-name">${userName}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="profile-dropdown">
                    <div class="profile-summary">
                        <div class="summary-name">${userName}</div>
                        <div class="summary-email">${user?.email || ''}</div>
                    </div>
                    <a href="profile.html" class="dropdown-item"><i class="fas fa-user"></i> View / Edit Profile</a>
                    <a href="orders.html" class="dropdown-item"><i class="fas fa-receipt"></i> Order History</a>
                    <hr/>
                    <a href="#" class="dropdown-item" id="logoutLink"><i class="fas fa-sign-out-alt"></i> Logout</a>
                </div>
            </div>
        `;
        wireProfileMenu();

        // Also create a small floating profile button so it's always visible
        ensureFloatingProfile((user && user.avatar) || 'https://i.pravatar.cc/60', 'profile.html');
    } else {
        // User is not logged in - show login and signup buttons
        authLinksContainer.innerHTML = `
            <a href="login.html" class="auth-btn-small">
                <i class="fas fa-sign-in-alt"></i> Login
            </a>
            <a href="signup.html" class="auth-btn-small primary">
                <i class="fas fa-user-plus"></i> Sign Up
            </a>
        `;
        // Show a small user icon that links to login
        ensureFloatingProfile('https://i.pravatar.cc/60?u=guest', 'login.html');
    }
}

function wireProfileMenu(){
    const trigger = document.querySelector('.profile-trigger');
    const dropdown = document.querySelector('.profile-dropdown');
    const logoutLink = document.getElementById('logoutLink');
    if (!trigger || !dropdown) return;
    trigger.addEventListener('click', function(){
        const expanded = this.getAttribute('aria-expanded') === 'true';
        this.setAttribute('aria-expanded', (!expanded).toString());
        dropdown.classList.toggle('open');
    });
    document.addEventListener('click', function(e){
        if (!e.target.closest('.profile-menu')){
            dropdown.classList.remove('open');
            trigger.setAttribute('aria-expanded', 'false');
        }
    });
    if (logoutLink){
        logoutLink.addEventListener('click', handleLogout);
    }
}

function ensureFloatingProfile(avatarUrl, href){
    if (document.querySelector('.profile-fab')) return;
    const fab = document.createElement('a');
    fab.className = 'profile-fab';
    fab.href = href || 'profile.html';
    fab.title = 'Your Profile';
    fab.innerHTML = `<img src="${avatarUrl}" alt="Profile"/>`;
    document.body.appendChild(fab);
}

async function handleLogout(event) {
    event.preventDefault();
    
    try {
        const API_BASE = 'http://localhost:5000/api';
        const response = await fetch(`${API_BASE}/logout`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear local storage
            localStorage.clear();
            
            // Show success message if showAlert is available
            if (window.authUtils && window.authUtils.showAlert) {
                window.authUtils.showAlert('success', 'Logged out successfully!', 'fas fa-check-circle');
            }
            
            // Update navigation
            updateAuthNavigation();
            
            // Redirect to home page after short delay
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            throw new Error(result.message || 'Logout failed');
        }
    } catch (error) {
        console.error('Logout error:', error);
        
        // Show error message if showAlert is available
        if (window.authUtils && window.authUtils.showAlert) {
            window.authUtils.showAlert('error', 'Logout failed. Please try again.', 'fas fa-exclamation-circle');
        } else {
            alert('Logout failed. Please try again.');
        }
    }
}

// Listen for storage changes (for multi-tab support)
window.addEventListener('storage', function(e) {
    if (e.key === 'isLoggedIn' || e.key === 'userName') {
        updateAuthNavigation();
    }
});

// Export function for use in other scripts
window.navigationAuth = {
    updateAuthNavigation,
    handleLogout
};