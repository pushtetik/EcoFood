

const MAX_QUANTITY = 100;

Cart.prototype.renderCartPageItems = function() {
    const container = document.getElementById('cartPageItems');
    if (!container) return;

    container.innerHTML = '';

    this.items.forEach((item, index) => {
        const isMaxQuantity = item.quantity >= MAX_QUANTITY;
        const isMobile = window.innerWidth <= 768;
        
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-page-item';
        
        if (isMobile) {
            itemElement.innerHTML = `
                <div class="mobile-cart-item">
                    <div class="mobile-item-header">
                        <div class="mobile-item-image">
                            <a href="/catalog/${item.id}/" class="product-link">
                                <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                            </a>
                        </div>
                        <div class="mobile-item-info">
                            <a href="/catalog/${item.id}/" class="product-link">
                                <h5 class="product-name">${item.name}</h5>
                            </a>
                            <div class="product-description">
                                ${item.description || 'Свежий и качественный продукт. Идеально подходит для здорового питания.'}
                            </div>
                            <div class="product-price">${(item.price * item.quantity).toLocaleString()} ₽</div>
                        </div>
                    </div>
                    <div class="mobile-item-actions">
                        <div class="mobile-quantity-section">
                            <div class="mobile-quantity-controls">
                                <button class="quantity-btn" onclick="cart.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                                <input type="number" class="quantity-input" value="${item.quantity}" 
                                       min="1" max="${MAX_QUANTITY}" onchange="cart.updateQuantity(${item.id}, parseInt(this.value))">
                                <button class="quantity-btn" ${isMaxQuantity ? 'disabled' : ''} onclick="cart.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            </div>
                            <div class="mobile-delete-section">
                                <button class="btn btn-outline-danger" 
                                        onclick="cart.removeItem(${item.id})">
                                    <i class="bi bi-trash"></i> Удалить
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            itemElement.innerHTML = `
                <div class="desktop-cart-item">
                    <div class="desktop-item-image">
                        <a href="/catalog/${item.id}/" class="product-link">
                            <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                        </a>
                    </div>
                    <div class="desktop-item-info">
                        <a href="/catalog/${item.id}/" class="product-link">
                            <h5 class="product-name">${item.name}</h5>
                        </a>
                        <div class="product-description">
                            ${item.description || 'Свежий и качественный продукт. Идеально подходит для здорового питания.'}
                        </div>
                        <div class="product-price">${(item.price * item.quantity).toLocaleString()} ₽</div>
                    </div>
                    <div class="desktop-item-actions">
                        <div class="desktop-quantity-section">
                            <div class="quantity-controls">
                                <button class="quantity-btn" onclick="cart.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                                <input type="number" class="quantity-input" value="${item.quantity}" 
                                       min="1" max="${MAX_QUANTITY}" onchange="cart.updateQuantity(${item.id}, parseInt(this.value))">
                                <button class="quantity-btn" ${isMaxQuantity ? 'disabled' : ''} onclick="cart.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            </div>
                        </div>
                        <div class="delete-section">
                            <button class="btn btn-outline-danger" 
                                    onclick="cart.removeItem(${item.id})">
                                <i class="bi bi-trash"></i> Удалить
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.appendChild(itemElement);
    });
};

Cart.prototype.updateQuantity = function(productId, newQuantity) {
    if (newQuantity <= 0) {
        this.removeItem(productId);
        return;
    }
    
    if (newQuantity > MAX_QUANTITY) {
        this.showNotification(`Максимальное количество товара - ${MAX_QUANTITY} шт.`, 'warning');
        newQuantity = MAX_QUANTITY;
    }
    
    const item = this.items.find(item => item.id === productId);
    if (item) {
        item.quantity = newQuantity;
        this.save();
        this.updateCartDisplay();
    
        if (window.location.pathname.includes('/cart/')) {
            this.updateCartPage();
        }
    }
};

Cart.prototype.addItem = function(product) {
    const existingItem = this.items.find(item => item.id === product.id);
    
    if (existingItem) {
        const newQuantity = existingItem.quantity + (product.quantity || 1);
        if (newQuantity > MAX_QUANTITY) {
            this.showNotification(`Максимальное количество товара - ${MAX_QUANTITY} шт.`, 'warning');
            existingItem.quantity = MAX_QUANTITY;
        } else {
            existingItem.quantity = newQuantity;
        }
    } else {
        this.items.push({
            ...product,
            quantity: product.quantity || 1
        });
    }
    
    this.save();
    this.updateCartDisplay();
    this.showNotification('Товар добавлен в корзину!', 'success');
};


function clearCart() {
    if (window.cart) {
        window.cart.clear();
        window.cart.updateCartPage();
    }
}


let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        if (window.location.pathname.includes('/cart/') && window.cart) {
            window.cart.renderCartPageItems();
        }
    }, 250);
});


document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('/cart/')) {
 
        if (window.cart) {
            window.cart.updateCartPage();
        }
    }
});
