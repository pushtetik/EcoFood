from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    list_display = ('phone', 'email', 'first_name', 'show_password')
    
    readonly_fields = ('show_password',)
    
    ordering = ('phone',)

    search_fields = ('phone', 'email', 'first_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    fieldsets = (
        (None, {'fields': ('phone', 'password', 'show_password')}),
        ('Персональная информация', {'fields': ('first_name', 'email', 'date_of_birth')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'email', 'first_name', 'date_of_birth', 'password1', 'password2'),
        }),
    )
    
    def show_password(self, obj):
     
        return obj.password
    show_password.short_description = 'Пароль'

@admin.register(User)
class UserAdmin(CustomUserAdmin):
    pass