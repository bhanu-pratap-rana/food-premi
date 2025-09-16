// Image loading error handling and fallbacks
function handleImageError(img) {
    console.log('Image failed to load:', img.src);
    
    // Add error class for styling
    img.classList.add('error');
    img.classList.remove('loading');
    
    // Create fallback content
    const fallbackDiv = document.createElement('div');
    fallbackDiv.style.cssText = `
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #f0f7f0, #e8f5e8);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        color: #666;
        font-size: 14px;
        text-align: center;
        position: absolute;
        top: 0;
        left: 0;
        z-index: 2;
    `;
    
    const icon = document.createElement('div');
    icon.innerHTML = '🍽️';
    icon.style.fontSize = '48px';
    icon.style.marginBottom = '8px';
    
    const text = document.createElement('div');
    text.textContent = 'Image not available';
    
    fallbackDiv.appendChild(icon);
    fallbackDiv.appendChild(text);
    
    // Insert fallback into image container
    const container = img.parentElement;
    if (container && container.classList.contains('item-image')) {
        container.appendChild(fallbackDiv);
        img.style.display = 'none';
    }
}

function handleImageLoad(img) {
    img.classList.remove('loading', 'error');
}

// Initialize image loading handlers
function initializeImages() {
    const images = document.querySelectorAll('.item-image img, .item-thumb');
    
    images.forEach(img => {
        // Add loading class initially
        img.classList.add('loading');
        
        // Set up event handlers
        img.addEventListener('load', () => handleImageLoad(img));
        img.addEventListener('error', () => handleImageError(img));
        
        // Check if image is already loaded
        if (img.complete && img.naturalHeight !== 0) {
            handleImageLoad(img);
        } else if (img.complete && img.naturalHeight === 0) {
            handleImageError(img);
        }
    });
}

// Active navigation highlighting
const navItems = document.querySelectorAll('.menu-nav-item');
const allSections = document.querySelectorAll('.category-section');
// Only track sections that are represented in the nav
const targetIds = Array.from(navItems).map(i => i.getAttribute('href').substring(1));
const sections = Array.from(allSections).filter(s => targetIds.includes(s.id));

// Smooth scrolling for navigation
function setActiveNav(id){
    navItems.forEach(n => n.classList.remove('active'));
    const active = Array.from(navItems).find(n => n.getAttribute('href').substring(1) === id);
    if (active) active.classList.add('active');
}

function scrollToSection(section){
    const y = section.getBoundingClientRect().top + window.pageYOffset - 90; // offset for sticky nav
    window.scrollTo({ top: y, behavior: 'smooth' });
}

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = item.getAttribute('href').substring(1);
        const targetSection = document.getElementById(targetId);
        if (targetSection) {
            setActiveNav(targetId);
            scrollToSection(targetSection);
        }
    });
});

// Create animated sparkles in the header
function createSparkles() {
    const header = document.querySelector('header');
    if (!header) return;
    
    const headerRect = header.getBoundingClientRect();
    
    // Create 15 sparkles with random positions, sizes and animation delays
    for (let i = 0; i < 15; i++) {
        const sparkle = document.createElement('div');
        sparkle.classList.add('sparkle');
        
        // Random size between 3px and 7px
        const size = Math.random() * 4 + 3;
        sparkle.style.width = `${size}px`;
        sparkle.style.height = `${size}px`;
        
        // Random position within the header
        const left = Math.random() * (headerRect.width - 20);
        const top = Math.random() * (headerRect.height - 20);
        sparkle.style.left = `${left}px`;
        sparkle.style.top = `${top}px`;
        
        // Random animation delay
        sparkle.style.animationDelay = `${Math.random() * 5}s`;
        
        header.appendChild(sparkle);
    }
}

// Back to top button visibility
const backToTopButton = document.querySelector('.back-to-top');

// Active navigation highlighting on scroll
function updateActiveNavOnScroll() {
    if (backToTopButton && window.scrollY > 300) {
        backToTopButton.classList.add('visible');
    } else if (backToTopButton) {
        backToTopButton.classList.remove('visible');
    }
    
    // Find the section currently in view
    const scrollPosition = window.scrollY + 150; // Offset for sticky nav
    
    let activeSection = sections[0]?.id || '';
    
    for (let i = 0; i < sections.length; i++) {
        const section = sections[i];
        const sectionTop = section.offsetTop;
        const sectionBottom = sectionTop + section.offsetHeight;
        
        if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
            activeSection = section.id;
            break;
        }
    }
    
    // Only update if different to avoid unnecessary DOM updates
    const currentActive = document.querySelector('.menu-nav-item.active');
    const targetActive = document.querySelector(`[href="#${activeSection}"]`);
    
    if (currentActive !== targetActive) {
        setActiveNav(activeSection);
    }
}

// Throttled scroll handler for better performance
let scrollTimeout;
const stickyNav = document.querySelector('.menu-navigation');
window.addEventListener('scroll', function() {
    if (scrollTimeout) clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
        updateActiveNavOnScroll();
        if (stickyNav) {
            if (window.scrollY > 40) stickyNav.classList.add('scrolled');
            else stickyNav.classList.remove('scrolled');
        }
    }, 10);
});

// Back to top functionality
if (backToTopButton) {
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Create sparkles when the page loads
document.addEventListener('DOMContentLoaded', function() {
    createSparkles();
    initializeImages(); // Initialize image error handling
    
    // Add animation classes to menu items on load and as they appear in viewport
    const menuItems = document.querySelectorAll('.menu-item');
    
    // Initial animation for visible items
    menuItems.forEach((item, index) => {
        setTimeout(() => {
            item.classList.add('animate-in');
        }, 100 * index);
    });
    
    // Intersection observer for scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    menuItems.forEach(item => {
        observer.observe(item);
    });
    
    // Add 'Add to Cart' buttons to all menu items
    const priceOptions = document.querySelectorAll('.price-option');
    priceOptions.forEach(option => {
        // Check if 'Add to Cart' button already exists
        if (!option.querySelector('.add-to-cart')) {
            const priceElement = option.querySelector('.price');
            const price = priceElement ? priceElement.textContent.replace('₹', '') : '0';
            const sizeElement = option.querySelector('.size-label');
            const size = sizeElement ? sizeElement.textContent : 'Regular';
            
            // Find parent menu item to get name and image
            const menuItem = option.closest('.menu-item');
            const nameElement = menuItem.querySelector('.item-name');
            const name = nameElement ? nameElement.textContent : 'Item';
            const imageElement = menuItem.querySelector('.item-image img');
            const image = imageElement ? imageElement.getAttribute('src') : '';
            
            // Create Add to Cart button
            const addToCartBtn = document.createElement('button');
            addToCartBtn.classList.add('add-to-cart');
            addToCartBtn.setAttribute('data-name', name);
            addToCartBtn.setAttribute('data-price', price);
            addToCartBtn.setAttribute('data-size', size);
            addToCartBtn.setAttribute('data-image', image);
            addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> Add';
            
            // Append button to price option
            option.appendChild(addToCartBtn);
        }
    });

    // Shopping Cart Functionality
    let cart = [];
    
    // DOM Elements
    const cartIcon = document.querySelector('.cart-icon');
    const cartCount = document.querySelector('.cart-count');
    const cartModal = document.querySelector('.cart-modal');
    const cartClose = document.querySelector('.cart-close');
    const cartItems = document.querySelector('.cart-items');
    const cartEmpty = document.querySelector('.cart-empty');
    const subtotalValue = document.querySelector('.subtotal-value');
    const taxValue = document.querySelector('.tax-value');
    const totalValue = document.querySelector('.total-value');
    const clearCartBtn = document.querySelector('.clear-cart');
    const proceedCheckoutBtn = document.querySelector('.proceed-checkout');
    
    // Checkout Elements
    const checkoutModal = document.querySelector('.checkout-modal');
    const checkoutClose = document.querySelector('.checkout-close');
    const orderItems = document.querySelector('.order-items');
    const checkoutTotalValue = document.querySelector('.checkout-total-value');
    const confirmPaymentBtn = document.querySelector('.confirm-payment');
    
    // Confirmation Elements
    const confirmationModal = document.querySelector('.confirmation-modal');
    const backToMenuBtn = document.querySelector('.back-to-menu');

    // API base for orders persistence
    const API_BASE = (window.API_BASE || 'http://localhost:5000/api');

    function computeTotals() {
        const subtotal = cart.reduce((sum, it) => sum + (it.price * it.quantity), 0);
        const tax = Math.round(subtotal * 0.05);
        const total = subtotal + tax;
        return { subtotal, tax, total };
    }

    async function persistOrderIfPossible() {
        try {
            // Try to persist order for logged-in users
            const totals = computeTotals();
            const extras = collectOrderExtras();
            const payload = {
                items: cart.map(it => ({
                    name: it.name,
                    size: it.size,
                    price: it.price,
                    quantity: it.quantity,
                    image: it.image
                })),
                subtotal: totals.subtotal,
                tax: totals.tax,
                total_amount: totals.total,
                channel: 'web',
                address: extras.address,
                notes: extras.notes,
                customer_name: (localStorage.getItem('userName') || (window.__profile && window.__profile.name) || extras.guestName || ''),
                customer_phone: ((window.__profile && window.__profile.phone) || extras.guestPhone || '')
            };
            const res = await fetch(`${API_BASE}/orders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) return { orderId: null };
            const json = await res.json();
            return { orderId: json.order_id || null };
        } catch (e) {
            console.warn('Order persistence skipped:', e);
            return { orderId: null };
        }
    }

    function buildWhatsAppMessage(orderId) {
        const { subtotal, tax, total } = computeTotals();
        const extras = collectOrderExtras();
        const userName = (localStorage.getItem('userName') || (window.__profile && window.__profile.name) || extras.guestName || 'Guest');
        const userPhone = ((window.__profile && window.__profile.phone) || extras.guestPhone || '');
        let lines = [];
        lines.push('New order from Food Premi');
        lines.push(`Name: ${userName}`);
        if (orderId) lines.push(`Order ID: ${orderId}`);
        lines.push('');
        lines.push('Items:');
        cart.forEach((it, idx) => {
            const lineTotal = it.price * it.quantity;
            lines.push(`${idx + 1}) ${it.name} (${it.size}) x ${it.quantity} - Rs ${it.price} = Rs ${lineTotal}`);
        });
        lines.push('');
        lines.push(`Subtotal: Rs ${subtotal}`);
        lines.push(`Tax (5%): Rs ${tax}`);
        lines.push(`Total: Rs ${total}`);
        if (extras.address) lines.push(``);
        if (extras.address) lines.push(`Address: ${extras.address}`);
        if (userPhone) lines.push(`Phone: ${userPhone}`);
        if (extras.notes) lines.push(`Notes: ${extras.notes}`);
        lines.push('');
        lines.push('Motto: GOOD FOR BODY, GREAT FOR SOUL');
        return lines.join('\n');
    }

    function openWhatsAppWithMessage(orderId) {
        const phone = '+918171203683';
        const text = buildWhatsAppMessage(orderId);
        const url = `https://wa.me/${encodeURIComponent(phone)}?text=${encodeURIComponent(text)}`;
        window.open(url, '_blank');
    }

    // Ensure address/notes inputs and extra actions exist in checkout
    function ensureCheckoutExtrasUI(){
        if (!checkoutModal) return;
        const container = checkoutModal.querySelector('.checkout-content');
        if (!container) return;
        if (!container.querySelector('#orderAddress')){
            const extras = document.createElement('div');
            extras.className = 'order-extras';
            extras.innerHTML = `
                <div style="margin:10px 0;">
                    <label style="display:block;margin-bottom:6px;">Delivery Address</label>
                    <textarea id="orderAddress" rows="2" placeholder="Your address (optional)" style="width:100%;padding:8px;border:1px solid #e0e0e0;border-radius:8px;"></textarea>
                </div>
                <div style="margin:10px 0;">
                    <label style="display:block;margin-bottom:6px;">Notes</label>
                    <input id="orderNotes" type="text" placeholder="Any special instructions (optional)" style="width:100%;padding:8px;border:1px solid #e0e0e0;border-radius:8px;"/>
                </div>
                <div style="display:flex;gap:10px;margin-top:10px;">
                    <button class="preview-message btn outline" type="button" style="padding:8px 12px;border-radius:8px;">Preview Message</button>
                    <button class="place-order btn" type="button" style="padding:8px 12px;border-radius:8px;background:#4CAF50;color:#fff;border:none;">Place Order (No WhatsApp)</button>
                </div>
            `;
            container.appendChild(extras);
        }
    }

    function collectOrderExtras(){
        const addressEl = document.getElementById('orderAddress');
        const notesEl = document.getElementById('orderNotes');
        return {
            address: addressEl ? addressEl.value.trim() : '',
            notes: notesEl ? notesEl.value.trim() : ''
        };
    }

    function showMessagePreview(text){
        // lightweight modal overlay
        let modal = document.querySelector('.message-preview-modal');
        if (!modal){
            modal = document.createElement('div');
            modal.className = 'message-preview-modal';
            modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:9999;';
            modal.innerHTML = `
                <div style="background:#fff;max-width:600px;width:90%;padding:16px;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,0.2);">
                    <h3 style="margin-top:0;">WhatsApp Message Preview</h3>
                    <textarea class="preview-text" style="width:100%;height:200px;padding:8px;border:1px solid #e0e0e0;border-radius:8px;white-space:pre;">${text}</textarea>
                    <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:10px;">
                        <button class="copy-btn" style="padding:8px 12px;border-radius:8px;border:1px solid #cfd8dc;background:#fff;">Copy</button>
                        <button class="close-btn" style="padding:8px 12px;border-radius:8px;background:#4CAF50;color:#fff;border:none;">Close</button>
                    </div>
                </div>`;
            document.body.appendChild(modal);
            modal.addEventListener('click', (e)=>{
                if (e.target.classList.contains('close-btn') || e.target === modal){
                    modal.remove();
                }
                if (e.target.classList.contains('copy-btn')){
                    const t = modal.querySelector('.preview-text');
                    t.select();
                    document.execCommand('copy');
                }
            });
        } else {
            const t = modal.querySelector('.preview-text');
            t.value = text;
        }
    }

    // Enhance checkout UI on open
    if (proceedCheckoutBtn){
        proceedCheckoutBtn.addEventListener('click', ()=>{ ensureCheckoutExtrasUI(); prefillAddressFromProfile(); });
    }
    if (checkoutModal){
        checkoutModal.addEventListener('click', (e)=>{
            if (e.target && (e.target.classList && e.target.classList.contains('preview-message'))){
                const { address, notes } = collectOrderExtras();
                // Temporarily include extras in message
                const id = null;
                // Monkey patch message builder to add extras content
                const { subtotal, tax, total } = computeTotals();
                let message = buildWhatsAppMessage(id);
                if (address) message += `\nAddress: ${address}`;
                if (notes) message += `\nNotes: ${notes}`;
                showMessagePreview(message);
            }
            if (e.target && (e.target.classList && e.target.classList.contains('place-order'))){
                (async () => {
                    const extras = collectOrderExtras();
                    try {
                        const totals = computeTotals();
                        const payload = {
                            items: cart.map(it => ({ name: it.name, size: it.size, price: it.price, quantity: it.quantity, image: it.image })),
                            subtotal: totals.subtotal,
                            tax: totals.tax,
                            total_amount: totals.total,
                            channel: 'web-no-wa',
                            address: extras.address,
                            notes: extras.notes,
                            customer_name: (localStorage.getItem('userName') || (window.__profile && window.__profile.name) || extras.guestName || ''),
                            customer_phone: ((window.__profile && window.__profile.phone) || extras.guestPhone || '')
                        };
                        const res = await fetch(`${API_BASE}/orders`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
                        const json = await res.json();
                        if (!res.ok || !json.success){
                            throw new Error(json.message || 'Please login to place an order.');
                        }
                        if (checkoutModal) checkoutModal.style.display = 'none';
                        if (confirmationModal) confirmationModal.style.display = 'flex';
                        cart = [];
                        updateCart();
                    } catch (err){
                        if (window.authUtils && window.authUtils.showAlert){
                            window.authUtils.showAlert('error', err.message, 'fas fa-exclamation-circle');
                        } else {
                            alert(err.message);
                        }
                    }
                })();
            }
        });
    }

    async function prefillAddressFromProfile(){
        try {
            const s = await fetch(`${API_BASE}/auth-status`).then(r=>r.json());
            if (!s.logged_in) return;
            const prof = await fetch(`${API_BASE}/profile`).then(r=>r.json());
            if (prof && prof.success && prof.user && prof.user.address){
                const el = document.getElementById('orderAddress');
                if (el && !el.value){ el.value = prof.user.address; }
            }
            if (prof && prof.success && prof.user){
                window.__profile = prof.user;
                const nameEl = document.getElementById('orderName');
                const phoneEl = document.getElementById('orderPhone');
                if (nameEl && !nameEl.value) nameEl.value = prof.user.name || '';
                if (phoneEl && !phoneEl.value) phoneEl.value = prof.user.phone || '';
            }
        } catch(e){ /* ignore */ }
    }
    
    // Add to Cart Button Click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-to-cart') || e.target.parentElement.classList.contains('add-to-cart')) {
            const button = e.target.classList.contains('add-to-cart') ? e.target : e.target.parentElement;
            const name = button.getAttribute('data-name');
            const price = parseInt(button.getAttribute('data-price'));
            const size = button.getAttribute('data-size');
            const image = button.getAttribute('data-image');
            
            addToCart(name, price, size, image);
            
            // Show brief animation feedback
            button.classList.add('added');
            setTimeout(() => {
                button.classList.remove('added');
            }, 1000);
        }
    });
    
    // Add to Cart Function
    function addToCart(name, price, size, image) {
        // Check if item with same name and size already in cart
        const existingItemIndex = cart.findIndex(item => 
            item.name === name && item.size === size
        );
        
        if (existingItemIndex > -1) {
            // Increment quantity of existing item
            cart[existingItemIndex].quantity += 1;
        } else {
            // Add new item to cart
            cart.push({
                name: name,
                price: price,
                size: size,
                image: image,
                quantity: 1,
                id: Date.now() // unique ID
            });
        }
        
        // Update cart UI
        updateCart();
    }
    
    // Update Cart UI
    function updateCart() {
        if (!cartCount) return;
        
        // Update cart count
        const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
        cartCount.textContent = totalItems;
        
        // Show or hide empty cart message
        if (cart.length === 0) {
            if (cartEmpty) cartEmpty.style.display = 'block';
            if (cartItems) cartItems.style.display = 'none';
            const cartSummary = document.querySelector('.cart-summary');
            const cartActions = document.querySelector('.cart-actions');
            if (cartSummary) cartSummary.style.display = 'none';
            if (cartActions) cartActions.style.display = 'none';
        } else {
            if (cartEmpty) cartEmpty.style.display = 'none';
            if (cartItems) cartItems.style.display = 'block';
            const cartSummary = document.querySelector('.cart-summary');
            const cartActions = document.querySelector('.cart-actions');
            if (cartSummary) cartSummary.style.display = 'block';
            if (cartActions) cartActions.style.display = 'flex';
            
            // Clear current items
            if (cartItems) cartItems.innerHTML = '';
            
            // Add each item to the cart UI
            cart.forEach(item => {
                const cartItem = document.createElement('div');
                cartItem.classList.add('cart-item');
                cartItem.setAttribute('data-id', item.id);
                
                const itemTotal = item.price * item.quantity;
                
                cartItem.innerHTML = `
                    <div class="cart-item-image">
                        <img src="${item.image}" alt="${item.name}">
                    </div>
                    <div class="cart-item-details">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-size">Size: ${item.size}</div>
                        <div class="cart-item-price">₹${item.price} x ${item.quantity} = ₹${itemTotal}</div>
                    </div>
                    <div class="cart-item-actions">
                        <div class="cart-quantity">
                            <button class="quantity-btn quantity-decrease">-</button>
                            <span class="quantity-value">${item.quantity}</span>
                            <button class="quantity-btn quantity-increase">+</button>
                        </div>
                        <button class="cart-remove" data-id="${item.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                
                if (cartItems) cartItems.appendChild(cartItem);
            });
            
            // Calculate totals
            const subtotal = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
            const tax = Math.round(subtotal * 0.05);
            const total = subtotal + tax;
            
            // Update summary values
            if (subtotalValue) subtotalValue.textContent = `₹${subtotal}`;
            if (taxValue) taxValue.textContent = `₹${tax}`;
            if (totalValue) totalValue.textContent = `₹${total}`;
        }
    }
    
    // Cart interactions
    if (cartItems) {
        cartItems.addEventListener('click', function(e) {
            if (e.target.classList.contains('quantity-increase')) {
                const itemId = parseInt(e.target.closest('.cart-item').getAttribute('data-id'));
                const itemIndex = cart.findIndex(item => item.id === itemId);
                
                if (itemIndex > -1) {
                    cart[itemIndex].quantity += 1;
                    updateCart();
                }
            }
            
            if (e.target.classList.contains('quantity-decrease')) {
                const itemId = parseInt(e.target.closest('.cart-item').getAttribute('data-id'));
                const itemIndex = cart.findIndex(item => item.id === itemId);
                
                if (itemIndex > -1) {
                    if (cart[itemIndex].quantity > 1) {
                        cart[itemIndex].quantity -= 1;
                    } else {
                        cart.splice(itemIndex, 1);
                    }
                    updateCart();
                }
            }
            
            if (e.target.classList.contains('cart-remove') || e.target.parentElement.classList.contains('cart-remove')) {
                const removeBtn = e.target.classList.contains('cart-remove') ? e.target : e.target.parentElement;
                const itemId = parseInt(removeBtn.getAttribute('data-id'));
                
                // Remove item from cart
                cart = cart.filter(item => item.id !== itemId);
                updateCart();
            }
        });
    }
    
    // Clear Cart Button
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', function() {
            cart = [];
            updateCart();
        });
    }
    
    // Cart Modal interactions
    if (cartIcon) {
        cartIcon.addEventListener('click', function() {
            if (cartModal) {
                cartModal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
            }
        });
    }
    
    if (cartClose) {
        cartClose.addEventListener('click', function() {
            if (cartModal) {
                cartModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    if (cartModal) {
        cartModal.addEventListener('click', function(e) {
            if (e.target === cartModal) {
                cartModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    // Checkout functionality
    if (proceedCheckoutBtn) {
        proceedCheckoutBtn.addEventListener('click', function() {
            if (cartModal) cartModal.style.display = 'none';
            if (checkoutModal) checkoutModal.style.display = 'flex';
            
            if (orderItems) {
                orderItems.innerHTML = '';
                
                cart.forEach(item => {
                    const orderItem = document.createElement('div');
                    orderItem.classList.add('order-item');
                    
                    orderItem.innerHTML = `
                        <span>${item.name} (${item.size})</span>
                        <span>₹${item.price} x ${item.quantity}</span>
                    `;
                    
                    orderItems.appendChild(orderItem);
                });
            }
            
            // Calculate total
            const total = cart.reduce((total, item) => total + (item.price * item.quantity), 0) + 
                          Math.round(cart.reduce((total, item) => total + (item.price * item.quantity), 0) * 0.05);
            
            if (checkoutTotalValue) checkoutTotalValue.textContent = `₹${total}`;
        });
    }
    
    if (checkoutClose) {
        checkoutClose.addEventListener('click', function() {
            if (checkoutModal) {
                checkoutModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    if (checkoutModal) {
        checkoutModal.addEventListener('click', function(e) {
            if (e.target === checkoutModal) {
                checkoutModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
    
    if (confirmPaymentBtn) {
        confirmPaymentBtn.addEventListener('click', async function() {
            if (checkoutModal) checkoutModal.style.display = 'none';

            // Persist order if possible, then open WhatsApp with composed message
            const { orderId } = await persistOrderIfPossible();
            openWhatsAppWithMessage(orderId);

            if (confirmationModal) {
                // Inject a quick WhatsApp button in confirmation for retry
                const wrapper = confirmationModal.querySelector('.confirmation-content');
                if (wrapper && !wrapper.querySelector('.send-whatsapp')) {
                    const btn = document.createElement('button');
                    btn.className = 'send-whatsapp';
                    btn.innerHTML = '<i class="fab fa-whatsapp"></i> Send Order via WhatsApp';
                    btn.style.marginRight = '10px';
                    btn.addEventListener('click', () => openWhatsAppWithMessage(orderId));
                    const backBtn = wrapper.querySelector('.back-to-menu');
                    if (backBtn) {
                        wrapper.insertBefore(btn, backBtn);
                    } else {
                        wrapper.appendChild(btn);
                    }
                }
                confirmationModal.style.display = 'flex';
            }

            // Clear cart after placing order
            cart = [];
            updateCart();
        });
    }
    
    if (backToMenuBtn) {
        backToMenuBtn.addEventListener('click', function() {
            if (confirmationModal) {
                confirmationModal.style.display = 'none';
                document.body.style.overflow = 'auto';
                
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
        });
    }

    // Goal switcher for goal-based meals
    try {
        const goalOptions = document.querySelectorAll('.goal-option');
        const goalCards = document.querySelectorAll('#goal-plans .menu-item');
        const showGroup = (group) => {
            goalCards.forEach(c => {
                const belongs = c.getAttribute('data-goal-group') === group;
                c.style.display = belongs ? '' : 'none';
            });
        };
        // default
        const active = document.querySelector('.goal-option.active');
        if (active) showGroup(active.getAttribute('data-goal'));
        goalOptions.forEach(opt => {
            opt.addEventListener('click', () => {
                goalOptions.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                showGroup(opt.getAttribute('data-goal'));
            });
        });
    } catch(e) { console.warn('Goal switch init skipped', e); }



    // Load menu dynamically from API
    async function loadMenu() {
        try {
            const response = await fetch(`${API_BASE}/menu`);
            const data = await response.json();

            if (data.success && data.data.length > 0) {
                // Find the first menu grid (main menu section)
                const menuGrid = document.querySelector('.menu-grid');
                if (menuGrid) {
                    // Clear existing static content
                    menuGrid.innerHTML = '';

                    // Create menu items from API data
                    data.data.forEach(item => {
                        const menuItemHTML = `
                            <div class="menu-item">
                                ${item.badges ? item.badges.map(badge => `<span class="badge">${badge}</span>`).join('') : ''}
                                <div class="item-image">
                                    <img src="${item.image || 'https://via.placeholder.com/300x200?text=No+Image'}" alt="${item.name}" onerror="handleImageError(this)" onload="handleImageLoad(this)">
                                </div>
                                <div class="item-content">
                                    <h3 class="item-name">${item.name}</h3>
                                    <div class="item-rating">
                                        <span class="item-stars">★★★★★</span>
                                        <span class="item-rating-text">4.8 (125 reviews)</span>
                                    </div>
                                    <p class="item-description">${item.description}</p>
                                    <div class="item-prices">
                                        ${item.prices.map(price => `
                                            <div class="price-option" data-price="${price.price}" data-size="${price.size}">
                                                <div class="size-label">${price.size}</div>
                                                <div class="price">₹${price.price}</div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                        `;
                        menuGrid.insertAdjacentHTML('beforeend', menuItemHTML);
                    });

                    console.log(`Loaded ${data.data.length} menu items from API`);
                } else {
                    console.warn('Menu grid not found');
                }
            } else {
                console.warn('No menu data available from API');
            }
        } catch (error) {
            console.error('Failed to load menu from API:', error);
        }
    }

    // Load menu on page load
    loadMenu();

    // Collage slider removed per request
});

// Delivery Banner Click Handler
const deliveryBanner = document.querySelector('.delivery-banner');
if (deliveryBanner) {
    deliveryBanner.addEventListener('click', function() {
        window.open('https://wa.me/+918171203683?text=Hi%2C%20I%27d%20like%20to%20order%20food.', '_blank');
    });
}
