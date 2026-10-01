
class Cart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('cart')) || [];
        this.updateCartDisplay();
        this.initEventListeners();
    }

    initEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart-btn')) {
                this.addProductFromButton(e.target);
            }
        });
    }

    addProductFromButton(button) {
        const productId = parseInt(button.dataset.productId);
        const productName = button.dataset.productName;
        const productPrice = parseFloat(button.dataset.productPrice);
        const productImage = button.dataset.productImage;

        const product = {
            id: productId,
            name: productName,
            price: productPrice,
            image: productImage,
            quantity: 1
        };

        this.addItem(product);
        this.showAddToCartAnimation(button);
    }

    addItem(product) {
        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += product.quantity || 1;
        } else {
            this.items.push({
                ...product,
                quantity: product.quantity || 1
            });
        }
        
        this.save();
        this.updateCartDisplay();
        this.showNotification('Товар добавлен в корзину!', 'success');
    }

    removeItem(productId) {
        this.items = this.items.filter(item => item.id !== productId);
        this.save();
        this.updateCartDisplay();
        this.showNotification('Товар удален из корзины', 'info');
    }

    updateQuantity(productId, newQuantity) {
        if (newQuantity <= 0) {
            this.removeItem(productId);
            return;
        }
        
        const item = this.items.find(item => item.id === productId);
        if (item) {
            item.quantity = newQuantity;
            this.save();
            this.updateCartDisplay();
        }
    }

    clear() {
        this.items = [];
        this.save();
        this.updateCartDisplay();
        this.showNotification('Корзина очищена', 'info');
    }

    getTotalCount() {
        return this.items.reduce((total, item) => total + item.quantity, 0);
    }

    getTotalPrice() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    }

    save() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    }

    updateCartDisplay() {
        const totalCount = this.getTotalCount();
        
        const cartCounters = document.querySelectorAll('#cartCountMobile, #cartCount, #cartCountSidebar');
        cartCounters.forEach(element => {
            element.textContent = totalCount;
            if (totalCount > 0) {
                element.style.display = 'flex';
            } else {
                element.style.display = 'none';
            }
        });

        if (window.location.pathname.includes('/cart/')) {
            this.updateCartPage();
        }
    }

    updateCartPage() {
        const totalCount = this.getTotalCount();
        const totalPrice = this.getTotalPrice();

        const emptyCart = document.getElementById('cartPageEmpty');
        const cartContent = document.getElementById('cartPageContent');
        const checkoutBtn = document.getElementById('checkoutBtn');
        const clearCartBtn = document.getElementById('clearCartBtn');

        if (emptyCart && cartContent) {
            if (totalCount === 0) {
                emptyCart.style.display = 'block';
                cartContent.style.display = 'none';
                if (checkoutBtn) checkoutBtn.disabled = true;
                if (clearCartBtn) clearCartBtn.disabled = true;
            } else {
                emptyCart.style.display = 'none';
                cartContent.style.display = 'block';
                if (checkoutBtn) checkoutBtn.disabled = false;
                if (clearCartBtn) clearCartBtn.disabled = false;
                
                this.renderCartPageItems();
                
                const itemsCount = document.getElementById('itemsCount');
                const cartPageTotal = document.getElementById('cartPageTotal');
                const cartPageFinalTotal = document.getElementById('cartPageFinalTotal');
                
                if (itemsCount) itemsCount.textContent = totalCount;
                if (cartPageTotal) cartPageTotal.textContent = `${totalPrice.toLocaleString()} ₽`;
                if (cartPageFinalTotal) cartPageFinalTotal.textContent = `${totalPrice.toLocaleString()} ₽`;
            }
        }
    }

    renderCartPageItems() {
        const container = document.getElementById('cartPageItems');
        if (!container) return;

        container.innerHTML = '';

        this.items.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'cart-page-item';
            itemElement.innerHTML = `
                <div class="row align-items-center">
                    <div class="col-3 col-md-2">
                        <img src="${item.image}" alt="${item.name}" class="cart-item-img">
                    </div>
                    <div class="col-5 col-md-6">
                        <h5 class="mb-2 fw-bold">${item.name}</h5>
                        <p class="text-success mb-0 fs-5 fw-bold">${item.price.toLocaleString()} ₽</p>
                    </div>
                    <div class="col-4 col-md-4">
                        <div class="d-flex align-items-center justify-content-between">
                            <div class="quantity-controls">
                                <button class="quantity-btn" onclick="cart.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                                <input type="number" class="quantity-input" value="${item.quantity}" 
                                       min="1" onchange="cart.updateQuantity(${item.id}, parseInt(this.value))">
                                <button class="quantity-btn" onclick="cart.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                            </div>
                            <div class="text-end">
                                <strong class="fs-5 d-block text-success">${(item.price * item.quantity).toLocaleString()} ₽</strong>
                                <button class="btn btn-outline-danger btn-sm mt-2" 
                                        onclick="cart.removeItem(${item.id})">
                                    <i class="bi bi-trash"></i> Удалить
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(itemElement);
        });
    }

    showAddToCartAnimation(button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-check2"></i> Добавлено';
        button.classList.add('added-to-cart');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('added-to-cart');
        }, 2000);
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 1060;
            min-width: 300px;
        `;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.cart = new Cart();
});

function clearCart() {
    if (confirm('Вы уверены, что хотите очистить корзину?')) {
        window.cart.clear();
    }
}

function checkout() {
    if (window.cart.getTotalCount() === 0) {
        alert('Корзина пуста!');
        return;
    }
    alert('Функционал оформления заказа будет реализован позже!');
}
