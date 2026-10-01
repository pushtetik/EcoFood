
const DADATA_API_KEY = '40bc460af63c6d32023254539fc490eaa23b955e';
const DADATA_URL = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address';

let deliveryZones = null;
let deliveryCost = 0;
let isDeliveryAvailable = false;
let hasHouseNumber = false;
let selectedPaymentMethod = null;
let appliedPromocode = null;
let discountAmount = 0;

let ORDER_CREATE_URL = null;
let APPLY_PROMOCODE_URL = null;

/**
 * Основная инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    ORDER_CREATE_URL = window.ORDER_CREATE_URL || '/orders/create/';
    APPLY_PROMOCODE_URL = window.APPLY_PROMOCODE_URL || '/orders/apply-promocode/';
    
    initializeCheckoutModal();
});

/**
 * Инициализация модального окна оформления заказа
 */
function initializeCheckoutModal() {
    const checkoutModal = document.getElementById('checkoutModal');
    if (!checkoutModal) return;
    
    initializeAddressAutocomplete();
    initializePaymentMethods();
    initializePromocodeHandlers();
    initializeFormValidation();
    
    checkoutModal.addEventListener('show.bs.modal', function() {
        updateModalTotals();
    });
}

/**
 * Инициализация автодополнения адреса через DaData
 */
function initializeAddressAutocomplete() {
    const addressInput = document.getElementById('deliveryAddress');
    if (!addressInput) return;
    
    addressInput.addEventListener('input', function(event) {
        const query = event.target.value.trim();

        isDeliveryAvailable = false;
        hasHouseNumber = false;
        updateSubmitButtonState();
        hideHouseNumberWarning();
        
        if (query.length >= 3) {
            getAddressSuggestions(query);
        } else {
            hideSuggestions();
            
            if (query.length === 0) {
                const deliveryInfo = document.getElementById('deliveryInfo');
                if (deliveryInfo) deliveryInfo.classList.add('d-none');
                
                const deliveryPrice = document.getElementById('deliveryPrice');
                if (deliveryPrice) deliveryPrice.textContent = 'Расчет...';
            }
        }
    });
    
    addressInput.addEventListener('blur', function() {
        setTimeout(hideSuggestions, 200);
        const address = this.value.trim();
        if (address.length >= 3 && !hasHouseNumber) {
            if (checkHouseNumberByText(address)) {
                hideHouseNumberWarning();
            } else {
                showHouseNumberWarning();
            }
        }
    });
}

/**
 * Запрашивает адресные подсказки от DaData
 */
async function getAddressSuggestions(query) {
    try {
        const response = await fetch(DADATA_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Token ' + DADATA_API_KEY
            },
            body: JSON.stringify({
                query: query,
                count: 5,
                restrict_value: true,
                from_bound: { value: "city" },
                to_bound: { value: "house" }
            })
        });

        const data = await response.json();
        showSuggestions(data.suggestions);
    } catch (error) {
        console.error('Error fetching address suggestions:', error);
    }
}

/**
 * Отображает список подсказок под полем ввода адреса
 */
function showSuggestions(suggestions) {
    const container = document.getElementById('addressSuggestions');
    if (!container) return;

    if (!suggestions || suggestions.length === 0) {
        container.classList.add('d-none');
        return;
    }

    let html = '';
    for (const suggestion of suggestions) {
        const value = suggestion.value;
        const lon = suggestion.data.geo_lon;
        const lat = suggestion.data.geo_lat;
        const hasHouse = checkHouseNumber(suggestion.data);
        const houseIcon = hasHouse ? '✓' : '⚠';
        const houseTitle = hasHouse ? 'Есть номер дома' : 'Уточните номер дома';
        
        html += '<div class="suggestion-item" ' +
                'data-value="' + value + '" ' +
                'data-lon="' + lon + '" ' +
                'data-lat="' + lat + '" ' +
                'data-data="' + encodeURIComponent(JSON.stringify(suggestion.data)) + '" ' +
                'title="' + houseTitle + '">' +
                '<span class="me-2">' + houseIcon + '</span>' + value +
                '</div>';
    }

    container.innerHTML = html;
    container.classList.remove('d-none');

    const items = container.querySelectorAll('.suggestion-item');
    for (const item of items) {
        item.addEventListener('mousedown', function(event) {
            event.preventDefault();
            const address = item.getAttribute('data-value');
            const lon = parseFloat(item.getAttribute('data-lon'));
            const lat = parseFloat(item.getAttribute('data-lat'));
            const dataJson = item.getAttribute('data-data');
            const suggestionData = dataJson ? JSON.parse(decodeURIComponent(dataJson)) : null;
            selectSuggestion(address, lon, lat, suggestionData);
        });
    }
}

/**
 * Скрывает блок подсказок
 */
function hideSuggestions() {
    const container = document.getElementById('addressSuggestions');
    if (container) {
        container.classList.add('d-none');
    }
}

/**
 * При выборе подсказки — заполняем поле и проверяем зону доставки
 */
async function selectSuggestion(address, lon, lat, suggestionData) {
    const input = document.getElementById('deliveryAddress');
    if (input) {
        input.value = address;
    }
    hideSuggestions();
    await validateAddressAndDelivery(address, lon, lat, suggestionData);
}

/**
 * Проверяет, содержит ли адрес номер дома
 */
function checkHouseNumber(suggestionData) {
    if (suggestionData.house || suggestionData.house_type) {
        return true;
    }
    
    if (suggestionData.qc_house === '0' || suggestionData.qc_house === '1') {
        return true;
    }
    
    const addressLevel = suggestionData.qc_complete;
    if (addressLevel === '0' || addressLevel === '1') {
        return true;
    }
    
    return false;
}

/**
 * Проверяет адрес на наличие номера дома по тексту
 */
function checkHouseNumberByText(address) {
    const houseRegex = /(?:дом|д\.|д\s|дом\s|строение|стр\.|корпус|корп\.|к\.|литер|лит\.)\s*\d+[а-я]*|\d+\s*[а-я]?\s*(?:дом|д|строение|стр|корпус|корп|к|литер|лит)?/i;
    return houseRegex.test(address);
}

/**
 * Загружаем зоны доставки из файла data.geojson
 */
async function loadDeliveryZones() {
    if (deliveryZones !== null) {
        return deliveryZones;
    }
    try {
        const response = await fetch('/static/data.geojson');
        const jsonData = await response.json();
        deliveryZones = jsonData;
        return jsonData;
    } catch (error) {
        console.error('Error loading delivery zones:', error);
        return null;
    }
}

/**
 * Проверяем, находится ли точка внутри полигона
 */
function isPointInPolygon(point, polygon) {
    const x = point[0];
    const y = point[1];
    let inside = false;

    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const xi = polygon[i][0];
        const yi = polygon[i][1];
        const xj = polygon[j][0];
        const yj = polygon[j][1];

        const intersect = ((yi > y) !== (yj > y)) &&
            (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi);

        if (intersect) {
            inside = !inside;
        }
    }

    return inside;
}

/**
 * Определяем зону доставки по координатам точки
 */
async function getDeliveryZone(lon, lat) {
    const zones = await loadDeliveryZones();
    if (!zones || !zones.features) return null;

    for (const feature of zones.features) {
        if (feature.geometry.type === 'Polygon') {
            const coordinates = feature.geometry.coordinates[0];
            const pointInside = isPointInPolygon([lon, lat], coordinates);
            if (pointInside) {
                return feature.properties.description;
            }
        }
    }

    return null;
}

/**
 * Показывает предупреждение об отсутствии номера дома
 */
function showHouseNumberWarning() {
    const warningElement = document.getElementById('addressWarning');
    if (warningElement) {
        warningElement.classList.remove('d-none');
    }
    hasHouseNumber = false;
    updateSubmitButtonState();
}

/**
 * Скрывает предупреждение о номере дома
 */
function hideHouseNumberWarning() {
    const warningElement = document.getElementById('addressWarning');
    if (warningElement) {
        warningElement.classList.add('d-none');
    }
    hasHouseNumber = true;
    updateSubmitButtonState();
}

/**
 * Показывает сообщение об ошибке доставки
 */
function showDeliveryError() {
    const deliveryCostElement = document.getElementById('deliveryPrice');
    if (deliveryCostElement) {
        deliveryCostElement.innerHTML = '<span class="delivery-error">Доставка недоступна</span>';
    }
    
    const deliveryInfo = document.getElementById('deliveryInfo');
    if (deliveryInfo) {
        deliveryInfo.classList.remove('d-none');
    }
    
    const deliveryText = document.getElementById('deliveryText');
    if (deliveryText) {
        deliveryText.textContent = 'Доставка: ';
    }
    
    const deliveryCostSpan = document.getElementById('deliveryCost');
    if (deliveryCostSpan) {
        deliveryCostSpan.innerHTML = '<span class="delivery-error">Недоступна для данного адреса</span>';
    }
    
    isDeliveryAvailable = false;
    updateSubmitButtonState();
}

/**
 * Показывает успешную информацию о доставке
 */
function showDeliverySuccess(cost) {
    const deliveryCostElement = document.getElementById('deliveryPrice');
    if (deliveryCostElement) {
        if (cost === 0) {
            deliveryCostElement.innerHTML = '<span class="delivery-success">Бесплатно</span>';
        } else {
            deliveryCostElement.innerHTML = '<span class="delivery-success">' + cost + ' ₽</span>';
        }
    }
    
    const deliveryInfo = document.getElementById('deliveryInfo');
    if (deliveryInfo) {
        deliveryInfo.classList.remove('d-none');
    }
    
    const deliveryText = document.getElementById('deliveryText');
    if (deliveryText) {
        deliveryText.textContent = 'Доставка: ';
    }
    
    const deliveryCostSpan = document.getElementById('deliveryCost');
    if (deliveryCostSpan) {
        if (cost === 0) {
            deliveryCostSpan.innerHTML = '<span class="delivery-success">Бесплатно</span>';
        } else {
            deliveryCostSpan.innerHTML = '<span class="delivery-success">' + cost + ' ₽</span>';
        }
    }
    
    isDeliveryAvailable = true;
    updateSubmitButtonState();
}

/**
 * Проверяет адрес, вычисляет зону и стоимость доставки
 */
async function validateAddressAndDelivery(address, lon, lat, suggestionData = null) {
    if (!lon || !lat) {
        showDeliveryError();
        return;
    }

    if (suggestionData) {
        if (checkHouseNumber(suggestionData)) {
            hideHouseNumberWarning();
        } else {
            showHouseNumberWarning();
        }
    } else {
        if (checkHouseNumberByText(address)) {
            hideHouseNumberWarning();
        } else {
            showHouseNumberWarning();
        }
    }

    const zoneCost = await getDeliveryZone(lon, lat);
    const totalElement = document.getElementById('modalFinalTotal');
    const itemsTotal = window.cart ? window.cart.getTotalPrice() : 0;

    if (zoneCost !== null) {
        deliveryCost = parseInt(zoneCost);
        showDeliverySuccess(deliveryCost);
        
        const finalPrice = itemsTotal + deliveryCost - discountAmount;
        if (totalElement) {
            totalElement.textContent = finalPrice.toLocaleString() + ' ₽';
        }
    } else {
        deliveryCost = 0;
        showDeliveryError();
    }
}

// ==================== СПОСОБЫ ОПЛАТЫ ====================

/**
 * Инициализация выбора способа оплаты
 */
function initializePaymentMethods() {
    const paymentMethods = document.querySelectorAll('.payment-method');
    
    paymentMethods.forEach(method => {
        method.addEventListener('click', function() {
            paymentMethods.forEach(m => m.classList.remove('selected'));
      
            this.classList.add('selected');

            selectedPaymentMethod = this.getAttribute('data-method');
            const selectedMethodInput = document.getElementById('selectedPaymentMethod');
            if (selectedMethodInput) {
                selectedMethodInput.value = selectedPaymentMethod;
            }
 
            updateSubmitButtonState();
        });
    });
}

// ==================== ПРОМОКОДЫ ====================

/**
 * Инициализация обработчиков промокодов
 */
function initializePromocodeHandlers() {
    const promocodeInput = document.getElementById('promocodeInput');
    const applyPromocodeBtn = document.getElementById('applyPromocodeBtn');
    
    if (promocodeInput) {
        promocodeInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                applyPromocode();
            }
        });
    }
    
    if (applyPromocodeBtn) {
        applyPromocodeBtn.addEventListener('click', applyPromocode);
    }
}

/**
 * Применяет промокод
 */
async function applyPromocode() {
    const promocodeInput = document.getElementById('promocodeInput');
    const statusElement = document.getElementById('promocodeStatus');
    if (!promocodeInput || !statusElement) return;
    
    const promocode = promocodeInput.value.trim().toUpperCase();
    
    if (!promocode) {
        statusElement.innerHTML = '<span class="promocode-error">Введите промокод</span>';
        return;
    }
    
    const itemsTotal = window.cart ? window.cart.getTotalPrice() : 0;
    
    const cartItems = window.cart ? window.cart.items : [];
    
    statusElement.innerHTML = '<span class="text-muted">Проверяем промокод...</span>';
    
    try {
        const formData = new URLSearchParams();
        formData.append('promocode', promocode);
        formData.append('order_amount', itemsTotal);
        
        if (cartItems.length > 0) {
            formData.append('cart_data', JSON.stringify(cartItems));
        }
        
        const response = await fetch(APPLY_PROMOCODE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            appliedPromocode = {
                code: promocode,
                discount_percent: parseFloat(data.promocode?.discount_percent) || 0,
                discount_amount: parseFloat(data.discount) || 0,
                description: `Скидка ${data.promocode?.discount_percent || 0}%`
            };
            
            discountAmount = parseFloat(data.discount) || 0;
            
            statusElement.innerHTML = `<span class="promocode-success">
                ✅ Промокод "${promocode}" применен! Скидка ${data.promocode?.discount_percent || 0}%
            </span>`;
            
            promocodeInput.disabled = true;
            const applyPromocodeBtn = document.getElementById('applyPromocodeBtn');
            if (applyPromocodeBtn) {
                applyPromocodeBtn.disabled = true;
            }
            
            const appliedPromocodeInfo = document.getElementById('appliedPromocodeInfo');
            if (appliedPromocodeInfo) {
                appliedPromocodeInfo.classList.remove('d-none');
                document.getElementById('appliedPromocodeName').textContent = promocode;
                document.getElementById('appliedPromocodeDiscount').textContent = 
                    `-${data.promocode?.discount_percent || 0}%`;
            }
            
            const discountRow = document.getElementById('discountRow');
            if (discountRow) {
                discountRow.classList.remove('d-none');
                document.getElementById('discountAmount').textContent = `-${discountAmount.toLocaleString()} ₽`;
            }
            
            updateModalTotals();
            updateSubmitButtonState();
        } else {
            statusElement.innerHTML = `<span class="promocode-error">❌ ${data.message}</span>`;
        }
        
    } catch (error) {
        console.error('Error applying promocode:', error);
        statusElement.innerHTML = `<span class="promocode-error">❌ Ошибка при проверке промокода</span>`;
    }
}

/**
 * Удаляет примененный промокод
 */
function removePromocode() {
    appliedPromocode = null;
    discountAmount = 0;
    
    const promocodeInput = document.getElementById('promocodeInput');
    if (promocodeInput) {
        promocodeInput.value = '';
        promocodeInput.disabled = false;
    }
    
    const applyPromocodeBtn = document.getElementById('applyPromocodeBtn');
    if (applyPromocodeBtn) {
        applyPromocodeBtn.disabled = false;
    }
    
    const appliedPromocodeInfo = document.getElementById('appliedPromocodeInfo');
    if (appliedPromocodeInfo) {
        appliedPromocodeInfo.classList.add('d-none');
    }
    
    const discountRow = document.getElementById('discountRow');
    if (discountRow) {
        discountRow.classList.add('d-none');
    }
    
    const promocodeStatus = document.getElementById('promocodeStatus');
    if (promocodeStatus) {
        promocodeStatus.innerHTML = '';
    }

    updateModalTotals();

    updateSubmitButtonState();
}

// ==================== ВАЛИДАЦИЯ ФОРМЫ ====================

/**
 * Инициализация валидации формы
 */
function initializeFormValidation() {
    const apartmentInput = document.getElementById('apartment');
    if (apartmentInput) {
        apartmentInput.addEventListener('input', function() {
            validateApartmentField();
            updateSubmitButtonState();
        });
        
        apartmentInput.addEventListener('blur', function() {
            validateApartmentField();
        });
    }
}

/**
 * Валидация номера квартиры
 */
function validateApartment(apartment) {
    if (!apartment.trim()) {
        return true;
    }
    
    const apartmentRegex = /^\d+$/;
    return apartmentRegex.test(apartment.trim());
}

/**
 * Валидация поля квартиры с отображением ошибки
 */
function validateApartmentField() {
    const apartmentInput = document.getElementById('apartment');
    const apartmentError = document.getElementById('apartmentError');
    
    if (!apartmentInput || !apartmentError) return;
    
    const apartment = apartmentInput.value.trim();
    const isValid = validateApartment(apartment);
    
    if (apartment && !isValid) {
        apartmentError.classList.remove('d-none');
    } else {
        apartmentError.classList.add('d-none');
    }
    
    return isValid;
}

/**
 * Обновляет состояние кнопки оформления заказа
 */
function updateSubmitButtonState() {
    const submitBtn = document.getElementById('submitOrderBtn');
    const addressInput = document.getElementById('deliveryAddress');
    const apartmentInput = document.getElementById('apartment');

    if (!submitBtn || !addressInput || !apartmentInput) return;

    const apartment = apartmentInput.value.trim();
    const address = addressInput.value.trim();
    
    const isApartmentValid = validateApartment(apartment);

    const apartmentError = document.getElementById('apartmentError');
    if (apartmentError) {
        if (apartment && !isApartmentValid) {
            apartmentError.classList.remove('d-none');
        } else {
            apartmentError.classList.add('d-none');
        }
    }
    
    if (isDeliveryAvailable && address && hasHouseNumber && selectedPaymentMethod && isApartmentValid) {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-secondary');
        submitBtn.classList.add('btn-success');
    } else {
        submitBtn.disabled = true;
        submitBtn.classList.remove('btn-success');
        submitBtn.classList.add('btn-secondary');
    }
}

// ==================== РАСЧЕТ СУММ ====================


function updateModalTotals() {
    if (!window.cart) {
        return;
    }

    const itemsTotal = window.cart.getTotalPrice();
    const totalElement = document.getElementById('modalItemsTotal');
    const finalElement = document.getElementById('modalFinalTotal');

    if (totalElement) {
        totalElement.textContent = itemsTotal.toLocaleString() + ' ₽';
    }
    
    if (appliedPromocode) {
        const discountPercent = parseFloat(appliedPromocode.discount_percent) || 0;
  
        discountAmount = Math.round(itemsTotal * discountPercent / 100);
      
        if (isNaN(discountAmount) || !isFinite(discountAmount)) {
            discountAmount = 0;
        }
     
        const discountElement = document.getElementById('discountAmount');
        if (discountElement) {
            discountElement.textContent = '-' + discountAmount.toLocaleString() + ' ₽';
        }
    }
    
    const finalPrice = itemsTotal + deliveryCost - discountAmount;
    
    if (isNaN(finalPrice) || !isFinite(finalPrice)) {
        if (finalElement) {
            finalElement.textContent = 'Ошибка расчета';
        }
    } else if (finalElement) {
        finalElement.textContent = finalPrice.toLocaleString() + ' ₽';
    }
    
    updateSubmitButtonState();
}

// ==================== ОТПРАВКА ЗАКАЗА ====================

async function submitOrder() {
    const submitBtn = document.getElementById('submitOrderBtn');
    const addressInput = document.getElementById('deliveryAddress');
    const apartmentInput = document.getElementById('apartment');
    const commentInput = document.getElementById('deliveryComment');
    
    if (!submitBtn || !addressInput || !apartmentInput || !commentInput) return;
    
    const address = addressInput.value.trim();
    const apartment = apartmentInput.value.trim();
    const comment = commentInput.value.trim();

    if (!address) {
        showNotification('Введите адрес доставки!', 'danger');
        return;
    }
    
    if (!validateApartment(apartment)) {
        showNotification('Номер квартиры должен содержать только цифры!', 'danger');
        apartmentInput.focus();
        return;
    }
    
    if (!isDeliveryAvailable) {
        showNotification('Доставка недоступна для выбранного адреса!', 'danger');
        return;
    }

    if (!hasHouseNumber) {
        showNotification('Пожалуйста, уточните номер дома для доставки!', 'danger');
        return;
    }

    if (!selectedPaymentMethod) {
        showNotification('Выберите способ оплаты!', 'danger');
        return;
    }

    const cartItems = window.cart ? window.cart.items : [];
    if (!cartItems || cartItems.length === 0) {
        showNotification('Корзина пуста!', 'danger');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Оформляем...';

    try {
        const orderData = {
            address: address,
            apartment: apartment,
            delivery_comment: comment,
            payment_method: selectedPaymentMethod,
            delivery_cost: deliveryCost,
            cart_items: cartItems,
            promocode: appliedPromocode ? appliedPromocode.code : null,
            discount_amount: discountAmount,
            total_amount: window.cart ? window.cart.getTotalPrice() : 0
        };
        
        const response = await fetch(ORDER_CREATE_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(orderData)
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Заказ #${data.order_number} успешно оформлен!`, 'success');
            if (appliedPromocode) {
                removePromocode();
            }
            addressInput.value = '';
            apartmentInput.value = '';
            commentInput.value = '';

            selectedPaymentMethod = null;
            const paymentMethods = document.querySelectorAll('.payment-method');
            paymentMethods.forEach(m => m.classList.remove('selected'));
      
            isDeliveryAvailable = false;
            hasHouseNumber = false;
            deliveryCost = 0;

            const modalElement = document.getElementById('checkoutModal');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
            }

            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            }, 1500);
        } else {
    
            showNotification(data.message || 'Ошибка при оформлении заказа', 'danger');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Оформить заказ';
        }
    } catch (error) {
        console.error('Error submitting order:', error);
        showNotification('Произошла ошибка при отправке заказа', 'danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-bag-check me-2"></i>Оформить заказ';
    }
}

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 1060;
        min-width: 300px;
        animation: slideIn 0.3s ease-out;
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
    }, 5000);
}

window.CheckoutModule = {
    applyPromocode,
    removePromocode,
    submitOrder,
    updateModalTotals,
    showNotification,
    getCookie
};

window.applyPromocode = applyPromocode;
window.removePromocode = removePromocode;
window.submitOrder = submitOrder;