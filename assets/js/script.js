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
        confirmPaymentBtn.addEventListener('click', function() {
            if (checkoutModal) checkoutModal.style.display = 'none';
            if (confirmationModal) confirmationModal.style.display = 'flex';
            
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



    // Collage slider removed per request
});

// Delivery Banner Click Handler
const deliveryBanner = document.querySelector('.delivery-banner');
if (deliveryBanner) {
    deliveryBanner.addEventListener('click', function() {
        window.open('https://wa.me/+918171203683?text=Hi%2C%20I%27d%20like%20to%20order%20food.', '_blank');
    });
}