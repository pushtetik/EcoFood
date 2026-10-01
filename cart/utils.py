import json
from decimal import Decimal


def get_cart_items(request):
    """Получает товары из корзины из сессии"""
    cart_data = request.session.get('cart')
    if cart_data:
        try:
            return json.loads(cart_data)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def clear_cart(request):
    """Очищает корзину в сессии"""
    if 'cart' in request.session:
        del request.session['cart']
    request.session.modified = True


def add_to_cart(request, product_id, product_name, product_price, quantity=1):
    """Добавляет товар в корзину"""
    cart_items = get_cart_items(request)
    
    item_found = False
    for item in cart_items:
        if item.get('id') == product_id:
            item['quantity'] += quantity
            item_found = True
            break
    
    if not item_found:
        cart_items.append({
            'id': product_id,
            'name': product_name,
            'price': float(product_price),
            'quantity': quantity,
            'image': '' 
        })
    
    request.session['cart'] = json.dumps(cart_items)
    request.session.modified = True
    return cart_items


def remove_from_cart(request, product_id):
    """Удаляет товар из корзины"""
    cart_items = get_cart_items(request)
    cart_items = [item for item in cart_items if item.get('id') != product_id]
    
    request.session['cart'] = json.dumps(cart_items)
    request.session.modified = True
    return cart_items


def update_cart_item(request, product_id, quantity):
    """Обновляет количество товара в корзине"""
    cart_items = get_cart_items(request)
    
    for item in cart_items:
        if item.get('id') == product_id:
            if quantity <= 0:
                return remove_from_cart(request, product_id)
            item['quantity'] = quantity
            break
    
    request.session['cart'] = json.dumps(cart_items)
    request.session.modified = True
    return cart_items


def get_cart_total(request):
    """Возвращает общую сумму корзины"""
    cart_items = get_cart_items(request)
    total = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart_items)
    return Decimal(str(total))


def get_cart_count(request):
    """Возвращает общее количество товаров в корзине"""
    cart_items = get_cart_items(request)
    return sum(item.get('quantity', 0) for item in cart_items)