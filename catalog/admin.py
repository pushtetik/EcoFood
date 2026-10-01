from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'in_stock', 'image_preview']
    list_filter = ['category', 'in_stock']
    search_fields = ['name', 'description']
    list_editable = ['price', 'in_stock']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price', 'category')
        }),
        ('Изображение (выберите один вариант)', {
            'fields': ('image_file', 'image_url'),
            'description': 'Заполните ОДНО из полей: загрузите файл ИЛИ вставьте ссылку'
        }),
        ('Дополнительно', {
            'fields': ('old_price', 'in_stock'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image
            )
        return "—"
    image_preview.short_description = 'Изображение'