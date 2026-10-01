import uuid
import datetime
from django.db import models
from django.conf import settings  
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


class Order(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Наличными при получении'),
        ('card', 'Банковской картой онлайн'),
        ('card_courier', 'Картой курьеру'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('processing', 'В обработке'),
        ('cooking', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name='Пользователь'
    )
    order_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Номер заказа'
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Сумма товаров'
    )
    delivery_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Стоимость доставки'
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Сумма скидки'
    )
    final_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Итоговая сумма'
    )
    apartment = models.CharField(
        max_length=50, 
        verbose_name='Квартира/офис', 
        blank=True,
        default=''
    )
    delivery_comment = models.TextField(
        blank=True, 
        verbose_name='Комментарий к доставке',
        default=''
    )
    # Информация о доставке (убраны delivery_lat и delivery_lon)
    delivery_address = models.TextField(verbose_name='Адрес доставки')
    
    # Контактная информация
    customer_name = models.CharField(max_length=255, verbose_name='Имя получателя')
    customer_phone = models.CharField(max_length=20, verbose_name='Телефон получателя')
    customer_email = models.EmailField(blank=True, verbose_name='Email получателя')
    
    # Способ оплаты
    payment_method = models.CharField(
        max_length=100,
        choices=PAYMENT_METHODS,
        verbose_name='Способ оплаты'
    )
    
    promocode = models.ForeignKey(
        'Promocode',  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Промокод'
    )
    
    # Статус
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата доставки')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        phone = self.user.phone if hasattr(self.user, 'phone') else 'Без телефона'
        return f"Заказ #{self.order_number} от {phone}"
    
    def save(self, *args, **kwargs):
        # Автоматически генерируем номер заказа при создании
        if not self.order_number:
            self.order_number = f"ORD-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Автоматически рассчитываем итоговую сумму
        self.final_amount = self.total_amount + self.delivery_cost - self.discount_amount
        
        # Заполняем контактную информацию из профиля пользователя, если не указана
        if not self.customer_name and hasattr(self.user, 'first_name'):
            self.customer_name = self.user.first_name.strip()
        if not self.customer_phone and hasattr(self.user, 'phone'):
            self.customer_phone = self.user.phone
        if not self.customer_email and hasattr(self.user, 'email'):
            self.customer_email = self.user.email
        if not self.apartment:
            self.apartment = ''
        if not self.delivery_comment:
            self.delivery_comment = ''
        super().save(*args, **kwargs)
    
    def get_status_display_class(self):
        """Возвращает CSS класс для статуса"""
        status_classes = {
            'pending': 'warning',
            'processing': 'info',
            'cooking': 'primary',
            'delivering': 'info',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return status_classes.get(self.status, 'secondary')
    
    def get_payment_icon(self):
        """Возвращает иконку для способа оплаты"""
        icons = {
            'cash': 'bi-cash-coin',
            'card': 'bi-credit-card',
            'card_courier': 'bi-phone',
        }
        return icons.get(self.payment_method, 'bi-cash')
    
    def can_be_cancelled(self):
        """Проверяет, можно ли отменить заказ"""
        return self.status in ['pending', 'processing']
    
    def get_status_timeline(self):
        """Возвращает timeline статусов заказа"""
        timeline = [
            {
                'title': 'Заказ создан',
                'description': 'Заказ ожидает подтверждения',
                'status': 'completed',
                'date': self.created_at,
                'icon': '📦'
            }
        ]
        
        status_steps = [
            {
                'key': 'processing',
                'title': 'Заказ подтвержден',
                'description': 'Заказ принят в обработку',
                'icon': '✅'
            },
            {
                'key': 'cooking',
                'title': 'Заказ готовится',
                'description': 'Повара готовят ваш заказ',
                'icon': '👨‍🍳'
            },
            {
                'key': 'delivering',
                'title': 'Заказ в пути',
                'description': 'Курьер везет ваш заказ',
                'icon': '🚚'
            },
            {
                'key': 'delivered',
                'title': 'Заказ доставлен',
                'description': 'Заказ успешно доставлен',
                'icon': '🏠'
            }
        ]
        
        for step in status_steps:
            step_status = 'pending'
            step_date = None
            
            if self.status == step['key']:
                step_status = 'current'
            elif self.status in ['delivered', 'cancelled']:
                if step['key'] in ['processing', 'cooking', 'delivering', 'delivered']:
                    if self.status == 'delivered' or (self.status == 'cancelled' and self.status != step['key']):
                        step_status = 'completed'
                if step['key'] == 'delivered' and self.delivered_at:
                    step_date = self.delivered_at
            
            timeline.append({
                'title': step['title'],
                'description': step['description'],
                'status': step_status,
                'date': step_date,
                'icon': step['icon']
            })
        
        return timeline
    
    def get_full_address(self):
        """Возвращает полный адрес с квартирой"""
        full_address = self.delivery_address
        if self.apartment:
            full_address += f", кв. {self.apartment}"
        return full_address


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Заказ'
    )
    product_id = models.IntegerField(verbose_name='ID товара')
    product_name = models.CharField(max_length=255, verbose_name='Название товара')
    product_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена товара'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество'
    )
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Общая стоимость'
    )
    
    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.product_price * self.quantity
        super().save(*args, **kwargs)


class Promocode(models.Model):
    code = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name='Код промокода'
    )
    discount_percent = models.IntegerField(  
        verbose_name='Процент скидки',
        help_text='Например: 10 для 10% скидки'
    )
    min_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name='Минимальная сумма заказа',
        help_text='Минимальная сумма, с которой работает промокод'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    
    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} ({self.discount_percent}% от {self.min_order_amount}₽)"
    
    def is_valid(self, order_amount):
        """Проверяет валидность промокода"""
        if not self.is_active:
            return False, "Промокод неактивен"
        
        if order_amount < float(self.min_order_amount):
            return False, f"Минимальная сумма заказа для промокода: {self.min_order_amount} ₽"
        
        return True, "Промокод действителен"
    
    def calculate_discount(self, order_amount):
        """Рассчитывает скидку - исправленная версия"""
        try:
            from decimal import Decimal
            if not isinstance(order_amount, Decimal):
                try:
                    order_amount = Decimal(str(order_amount))
                except:
                    order_amount = Decimal('0')
            
            discount_percent_decimal = Decimal(str(self.discount_percent))
            discount = (order_amount * discount_percent_decimal) / Decimal('100')
            discount = discount.quantize(Decimal('0.01'))
            return discount
            
        except Exception as e:
            return Decimal('0.00')