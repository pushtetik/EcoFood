from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin import DateFieldListFilter
from django.contrib.auth import get_user_model
from django.http import HttpResponse
import csv
from io import StringIO
from .models import Order, OrderItem, Promocode

User = get_user_model()


class OrderItemInline(admin.TabularInline):
    """Встроенная админка для товаров в заказе"""
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'quantity']
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для заказов"""
    
    # Отображение в списке
    list_display = [
        'order_number', 
        'short_customer_info',
        'status_display', 
        'payment_method_display',
        'final_amount_display',
        'created_date',
        'quick_actions'
    ]
    
    # Фильтры
    list_filter = [
        'status',
        'payment_method',
        ('created_at', DateFieldListFilter),
        'promocode'
    ]
    
    # Поиск
    search_fields = [
        'order_number',
        'customer_name',
        'customer_phone',
        'delivery_address',
        'apartment',
        'user__phone',
        'user__email'
    ]
    
    # Только для чтения
    readonly_fields = [
        'order_number',
        'created_at',
        'updated_at',
        'delivered_at',
        'order_items_list',
        'full_address_display',
        'contact_info_display'
    ]
    
    # Группировка полей
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'order_number',
                'user',
                'status',
            )
        }),
        ('Контакты и доставка', {
            'fields': (
                'contact_info_display',
                'full_address_display',
                'delivery_comment',
            )
        }),
        ('Финансовая информация', {
            'fields': (
                'total_amount',
                'delivery_cost',
                'discount_amount',
                'final_amount',
                'payment_method',
                'promocode'
            ),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': (
                'delivered_at',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Встроенные формы
    inlines = [OrderItemInline]
    
    # Действия массового редактирования
    actions = [
        'mark_as_processing',
        'mark_as_cooking', 
        'mark_as_delivering',
        'mark_as_delivered',
        'mark_as_cancelled',
        'export_as_csv'
    ]

    list_per_page = 50
    
    # Иерархия по датам
    date_hierarchy = 'created_at'
    
    # Методы для отображения в списке
    
    def short_customer_info(self, obj):
        """Краткая информация о клиенте"""
        phone = obj.customer_phone or 'Без телефона'
        name = obj.customer_name or 'Без имени'
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            name,
            phone
        )
    short_customer_info.short_description = 'Клиент'
    
    def status_display(self, obj):
        """Цветное отображение статуса"""
        status_colors = {
            'pending': 'orange',
            'processing': 'blue',
            'cooking': 'purple',
            'delivering': 'cyan',
            'delivered': 'green',
            'cancelled': 'red',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="padding: 2px 8px; border-radius: 12px; background-color: {}; color: white; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    status_display.admin_order_field = 'status'
    
    def payment_method_display(self, obj):
        """Отображение способа оплаты с иконкой"""
        icons = {
            'cash': '💰',
            'card': '💳',
            'card_courier': '📱',
        }
        icon = icons.get(obj.payment_method, '❓')
        return f"{icon} {obj.get_payment_method_display()}"
    payment_method_display.short_description = 'Оплата'
    
    def final_amount_display(self, obj):
        """Отображение только итоговой суммы"""
        return format_html(
            '<div style="font-size: 14px; font-weight: bold;">{}₽</div>',
            obj.final_amount
        )
    final_amount_display.short_description = 'Сумма'
    final_amount_display.admin_order_field = 'final_amount'
    
    def created_date(self, obj):
        """Форматированная дата создания"""
        if obj.created_at:
            return obj.created_at.strftime('%d.%m.%Y %H:%M')
        return ''
    created_date.short_description = 'Дата создания'
    created_date.admin_order_field = 'created_at'
    
    def quick_actions(self, obj):
        """Быстрые кнопки действий для статусов"""
        if obj.status == 'pending':
            return format_html(
                '<a href="?action=confirm&id={}" class="button" style="background: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Подтвердить</a>'
                '<a href="?action=cancel&id={}" class="button" style="background: #f44336; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Отменить</a>',
                obj.id, obj.id
            )
        elif obj.status == 'processing':
            return format_html(
                '<a href="?action=cooking&id={}" class="button" style="background: #9C27B0; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Готовить</a>',
                obj.id
            )
        elif obj.status == 'cooking':
            return format_html(
                '<a href="?action=delivering&id={}" class="button" style="background: #00BCD4; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Курьеру</a>',
                obj.id
            )
        elif obj.status == 'delivering':
            return format_html(
                '<a href="?action=delivered&id={}" class="button" style="background: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Доставлен</a>',
                obj.id
            )
        return '-'
    quick_actions.short_description = 'Действия'
    
    # Методы для детального просмотра
    
    def order_items_list(self, obj):
        """Таблица товаров в заказе"""
        items = obj.items.all()
        html = '<div style="overflow-x: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">'
        html += '<thead><tr style="background-color: #f5f5f5;">'
        html += '<th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Товар</th>'
        html += '<th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">Кол-во</th>'
        html += '</tr></thead><tbody>'
        
        for item in items:
            html += format_html(
                '<tr style="border-bottom: 1px solid #eee;">'
                '<td style="padding: 10px;">{}</td>'
                '<td style="padding: 10px;">{}</td>'
                '</tr>',
                item.product_name,
                item.quantity
            )
        
        html += '</tbody></table></div>'
        return format_html(html)
    order_items_list.short_description = 'Состав заказа'
    
    def full_address_display(self, obj):
        """Отображение полного адреса с квартирой"""
        full_address = obj.delivery_address
        if obj.apartment:
            full_address += f", кв. {obj.apartment}"
        
        return format_html(
            '<div><strong>Адрес доставки:</strong><br>{}</div>',
            full_address
        )
    full_address_display.short_description = 'Адрес доставки'
    
    def contact_info_display(self, obj):
        """Отображение контактной информации"""
        return format_html(
            '<div>'
            '<strong>Имя:</strong> {}<br>'
            '<strong>Телефон:</strong> {}<br>'
            '<strong>Email:</strong> {}'
            '</div>',
            obj.customer_name,
            obj.customer_phone,
            obj.customer_email or 'не указан'
        )
    contact_info_display.short_description = 'Контактная информация'
    
    # Методы массовых действий
    
    def mark_as_processing(self, request, queryset):
        """Перевести в статус 'В обработке'"""
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} заказов переведены в статус 'В обработке'")
    mark_as_processing.short_description = "✅ Подтвердить выбранные"
    
    def mark_as_cooking(self, request, queryset):
        """Перевести в статус 'Готовится'"""
        updated = queryset.update(status='cooking')
        self.message_user(request, f"{updated} заказов переведены в статус 'Готовится'")
    mark_as_cooking.short_description = "🍳 Начать готовить"
    
    def mark_as_delivering(self, request, queryset):
        """Перевести в статус 'Доставляется'"""
        updated = queryset.update(status='delivering')
        self.message_user(request, f"{updated} заказов переведены в статус 'Доставляется'")
    mark_as_delivering.short_description = "🚚 Передать курьеру"
    
    def mark_as_delivered(self, request, queryset):
        """Отметить как доставленные"""
        count = queryset.count()
        queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f"{count} заказов отмечены как доставленные")
    mark_as_delivered.short_description = "✓ Доставлен"
    
    def mark_as_cancelled(self, request, queryset):
        """Отменить выбранные заказы"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} заказов отменены")
    mark_as_cancelled.short_description = "❌ Отменить"
    
    def export_as_csv(self, request, queryset):
        """Экспорт выбранных заказов в CSV"""
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        
        # Заголовки
        writer.writerow([
            'Номер заказа',
            'Дата создания',
            'Статус',
            'Клиент',
            'Телефон',
            'Email',
            'Адрес доставки',
            'Квартира/офис',
            'Комментарий к доставке',
            'Сумма товаров',
            'Стоимость доставки',
            'Скидка',
            'Итоговая сумма',
            'Способ оплаты',
            'Промокод',
            'Дата доставки'
        ])
        
        # Данные
        for order in queryset:
            writer.writerow([
                order.order_number,
                order.created_at.strftime('%d.%m.%Y %H:%M:%S'),
                order.get_status_display(),
                order.customer_name,
                order.customer_phone,
                order.customer_email or '',
                order.delivery_address,
                order.apartment,
                order.delivery_comment,
                str(order.total_amount),
                str(order.delivery_cost),
                str(order.discount_amount),
                str(order.final_amount),
                order.get_payment_method_display(),
                order.promocode.code if order.promocode else '',
                order.delivered_at.strftime('%d.%m.%Y %H:%M:%S') if order.delivered_at else ''
            ])
        
        output.seek(0)
        response = HttpResponse(output, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        return response
    export_as_csv.short_description = "📥 Экспорт в CSV"
    
    def changelist_view(self, request, extra_context=None):
        """Обработка быстрых действий из списка заказов"""
        action = request.GET.get('action')
        order_id = request.GET.get('id')
        
        if action and order_id:
            try:
                order = Order.objects.get(id=order_id)
                old_status = order.status
                
                if action == 'confirm' and order.status == 'pending':
                    order.status = 'processing'
                    order.save()
                    self.message_user(request, f"Заказ #{order.order_number} подтвержден", level='success')
                    
                elif action == 'cancel' and order.status in ['pending', 'processing']:
                    order.status = 'cancelled'
                    order.save()
                    self.message_user(request, f"Заказ #{order.order_number} отменен", level='warning')
                    
                elif action == 'cooking' and order.status == 'processing':
                    order.status = 'cooking'
                    order.save()
                    self.message_user(request, f"Заказ #{order.order_number} передан на кухню", level='success')
                    
                elif action == 'delivering' and order.status == 'cooking':
                    order.status = 'delivering'
                    order.save()
                    self.message_user(request, f"Заказ #{order.order_number} передан курьеру", level='success')
                    
                elif action == 'delivered' and order.status == 'delivering':
                    order.status = 'delivered'
                    order.delivered_at = timezone.now()
                    order.save()
                    self.message_user(request, f"Заказ #{order.order_number} отмечен как доставленный", level='success')
                    
                else:
                    self.message_user(request, f"Невозможно выполнить действие для статуса '{old_status}'", level='error')
                    
            except Order.DoesNotExist:
                self.message_user(request, "Заказ не найден", level='error')
        
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        """Оптимизация запросов с select_related и prefetch_related"""
        return super().get_queryset(request)\
            .select_related('user', 'promocode')\
            .prefetch_related('items')\
            .order_by('-created_at')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админка для позиций заказа"""
    
    list_display = [
        'order_link', 
        'product_name', 
        'quantity'
    ]
    
    list_filter = [
        'order__status',
    ]
    
    search_fields = [
        'product_name', 
        'order__order_number'
    ]
    
    readonly_fields = [
        'order', 
        'product_name', 
        'quantity'
    ]
    
    list_per_page = 50
    
    def order_link(self, obj):
        """Ссылка на заказ"""
        return format_html(
            '<a href="{}">#{}</a>',
            reverse("admin:orders_order_change", args=[obj.order.id]),
            obj.order.order_number
        )
    order_link.short_description = 'Заказ'
    order_link.admin_order_field = 'order'
    
    def has_add_permission(self, request):
        """Запрет на добавление"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Запрет на удаление"""
        return False
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related('order')


@admin.register(Promocode)
class PromocodeAdmin(admin.ModelAdmin):
    """Админка для промокодов"""
    
    list_display = [
        'code', 
        'discount_percent_display',
        'min_order_amount_display',
        'is_active_display',
        'usage_count'
    ]
    
    list_filter = [
        'is_active'
    ]
    
    search_fields = [
        'code'
    ]
    
    readonly_fields = ['usage_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'code', 
                'is_active'
            )
        }),
        ('Параметры скидки', {
            'fields': (
                'discount_percent', 
                'min_order_amount'
            )
        }),
        ('Статистика', {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 20
    
    actions = ['activate_promocodes', 'deactivate_promocodes']
    
    def discount_percent_display(self, obj):
        """Отображение процента скидки"""
        return format_html(
            '<span style="color: #4CAF50; font-weight: bold; font-size: 14px;">-{}%</span>',
            obj.discount_percent
        )
    discount_percent_display.short_description = 'Скидка'
    
    def min_order_amount_display(self, obj):
        """Отображение минимальной суммы заказа"""
        if obj.min_order_amount > 0:
            return format_html(
                '<span style="color: #666; font-size: 13px;">от {}₽</span>',
                obj.min_order_amount
            )
        return format_html('<span style="color: #666; font-size: 13px;">Любая сумма</span>')
    min_order_amount_display.short_description = 'Мин. сумма'
    
    def is_active_display(self, obj):
        """Индикатор активности"""
        if obj.is_active:
            return format_html(
                '<span style="color: #4CAF50; font-weight: bold;">✓ Активен</span>'
            )
        else:
            return format_html(
                '<span style="color: #F44336; font-weight: bold;">✗ Неактивен</span>'
            )
    is_active_display.short_description = 'Статус'
    
    def usage_count(self, obj):
        """Количество использований промокода"""
        count = obj.orders.count()
        return format_html(
            '<span style="font-size: 14px; font-weight: bold;">{}</span>',
            count
        )
    usage_count.short_description = 'Использован раз'
    
    def activate_promocodes(self, request, queryset):
        """Активировать промокоды"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} промокодов активировано")
    activate_promocodes.short_description = "✅ Активировать"
    
    def deactivate_promocodes(self, request, queryset):
        """Деактивировать промокоды"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} промокодов деактивировано")
    deactivate_promocodes.short_description = "❌ Деактивировать"
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request)