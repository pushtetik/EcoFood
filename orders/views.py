from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
import json
from decimal import Decimal

from .models import Order, OrderItem, Promocode
from .forms import OrderCreateForm, OrderCancelForm
from cart.utils import get_cart_items, clear_cart

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

@login_required
@require_POST
def create_order_from_modal(request):
    """Создание заказа из модального окна"""
    try:
        data = json.loads(request.body)
        
        # Получаем данные
        delivery_address = data.get('address')
        apartment = data.get('apartment', '')
        delivery_comment = data.get('delivery_comment', '')
        payment_method = data.get('payment_method')
        delivery_cost = data.get('delivery_cost', 0)
        cart_items = data.get('cart_items', [])
        promocode = data.get('promocode')
        discount_amount = data.get('discount_amount', 0)
       
        if apartment and not apartment.isdigit():
            return JsonResponse({
                'success': False,
                'message': 'Номер квартиры должен содержать только цифры'
            })

        # Проверяем что payment_method допустим
        valid_methods = ['cash', 'card', 'card_courier']
        
        # Если пришло русское название, преобразуем в ключ
        payment_method_map = {
            'Наличными при получении': 'cash',
            'Банковской картой онлайн': 'card',
            'Картой курьеру': 'card_courier'
        }
        
        if payment_method in payment_method_map:
            payment_method = payment_method_map[payment_method]
        
        if payment_method not in valid_methods:
            return JsonResponse({
                'success': False,
                'message': f'Недопустимый способ оплаты: {payment_method}. Допустимые: {", ".join(valid_methods)}'
            })
        
        # Проверяем обязательные поля
        if not delivery_address:
            return JsonResponse({
                'success': False,
                'message': 'Адрес доставки обязателен'
            })
        
        if not cart_items or len(cart_items) == 0:
            return JsonResponse({
                'success': False,
                'message': 'Корзина пуста'
            })
        
        # Рассчитываем суммы
        total_amount = 0
        for item in cart_items:
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            if price and quantity:
                total_amount += float(price) * int(quantity)
        
        if total_amount <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Сумма заказа должна быть больше нуля'
            })
        
        try:
            delivery_cost_value = float(delivery_cost)
        except (ValueError, TypeError):
            delivery_cost_value = 0.0
            
        try:
            discount_amount_value = float(discount_amount)
        except (ValueError, TypeError):
            discount_amount_value = 0.0
        
        # Определяем имя получателя
        customer_name = request.user.first_name or request.user.phone
        
        promo_obj = None
        
        # Применяем промокод если есть
        if promocode:
            try:
                promo_obj = Promocode.objects.get(code=promocode)
                if promo_obj.is_valid(total_amount):
                    calculated_discount = promo_obj.calculate_discount(total_amount)
                    discount_amount_value = float(calculated_discount)
                    
                else:
                    discount_amount_value = 0
                    promo_obj = None
    
            except Promocode.DoesNotExist:
        
                print(f"DEBUG: Promocode not found in database: {promocode}")
        final_amount = total_amount + delivery_cost_value - discount_amount_value
        
        # Создаем заказ
        order = Order(
            user=request.user,
            delivery_address=delivery_address,
            apartment=apartment,
            delivery_comment=delivery_comment,
            payment_method=payment_method,
            total_amount=Decimal(str(total_amount)),
            delivery_cost=Decimal(str(delivery_cost_value)),
            discount_amount=Decimal(str(discount_amount_value)),
            final_amount=Decimal(str(final_amount)),
            customer_name=customer_name,
            customer_phone=request.user.phone,
            customer_email=request.user.email or ''
        )
        
        # Устанавливаем промокод
        if promo_obj:
            order.promocode = promo_obj
        
        order.save()

        
        # Создаем позиции заказа
        for item in cart_items:
            product_id = item.get('id')
            product_name = item.get('name', 'Товар')
            product_price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            
            if not product_id or not product_name or not product_price:
                continue
            
            OrderItem.objects.create(
                order=order,
                product_id=product_id,
                product_name=product_name,
                product_price=Decimal(str(product_price)),
                quantity=quantity,
                total_price=Decimal(str(float(product_price) * quantity))
            )
        
        if 'cart' in request.session:
            del request.session['cart']
        if 'applied_promocode' in request.session:
            del request.session['applied_promocode']
        request.session.modified = True
    
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'discount_applied': float(order.discount_amount),
            'promocode_used': order.promocode.code if order.promocode else '',
            'redirect_url': reverse_lazy('orders:order_list')
        })
    
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False, 
            'message': f'Неверный формат данных: {str(e)}'
        })
    except Exception as e:
        import traceback
     
        return JsonResponse({
            'success': False, 
            'message': f'Произошла ошибка при создании заказа: {str(e)}'
        })
@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if not order.can_be_cancelled():
        messages.error(request, 'Нельзя отменить заказ в текущем статусе')
        return redirect('orders:order_list')
    
    order.status = 'cancelled'
    order.save()
    
    messages.success(request, f'Заказ #{order.order_number} отменен')
    return redirect('orders:order_list')

@login_required
@require_POST
def apply_promocode(request):
    if request.method == 'POST':
        code = request.POST.get('promocode', '').strip().upper()
        
        try:
            promocode = Promocode.objects.get(code=code)
            total_amount = 0
            try:
                total_amount = float(request.POST.get('order_amount', 0))
            except (ValueError, TypeError):
                pass
            if total_amount == 0:
                cart_data = request.POST.get('cart_data')
                if cart_data:
                    try:
                        cart_items = json.loads(cart_data)
                        total_amount = sum(
                            float(item.get('price', 0)) * int(item.get('quantity', 1))
                            for item in cart_items
                        )
                    except json.JSONDecodeError:
                        pass
            if total_amount == 0:
                cart_items = get_cart_items(request)
                total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
            is_valid, message = promocode.is_valid(total_amount)
            
            if is_valid:
                request.session['applied_promocode'] = {
                    'code': promocode.code,
                    'discount_percent': float(promocode.discount_percent),
                    'min_order_amount': float(promocode.min_order_amount),
                    'discount_amount': float(promocode.calculate_discount(total_amount))
                }
                request.session.modified = True
                
                return JsonResponse({
                    'success': True,
                    'message': f'Промокод "{code}" применен',
                    'discount': float(promocode.calculate_discount(total_amount)),
                    'promocode': {
                        'code': promocode.code,
                        'discount_percent': float(promocode.discount_percent),
                        'min_order_amount': float(promocode.min_order_amount)
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Promocode.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Промокод не найден'
            })
    
    return JsonResponse({'success': False, 'message': 'Неверный запрос'})
@login_required
def remove_promocode(request):
    if 'applied_promocode' in request.session:
        del request.session['applied_promocode']
        request.session.modified = True
    
    return JsonResponse({'success': True, 'message': 'Промокод удален'})