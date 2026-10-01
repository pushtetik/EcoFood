from django import forms
from .models import Order


class OrderCreateForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Комментарий к заказу (необязательно)',
            'class': 'form-control'
        }),
        required=False,
        label='Комментарий'
    )
    
    class Meta:
        model = Order
        fields = [
            'delivery_address',
            'delivery_comment',
            'payment_method',
            'customer_name',
            'customer_phone',
            'customer_email'
        ]
        widgets = {
            'delivery_address': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Введите полный адрес доставки'
            }),
            'delivery_comment': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Дополнительная информация для курьера'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя получателя'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Заполняем данные пользователя по умолчанию
        if user and user.is_authenticated:
            if not self.initial.get('customer_name') and user.first_name:
                self.initial['customer_name'] = f"{user.first_name} {user.last_name or ''}".strip()
            if not self.initial.get('customer_phone') and hasattr(user, 'phone'):
                self.initial['customer_phone'] = user.phone
            if not self.initial.get('customer_email') and user.email:
                self.initial['customer_email'] = user.email


class OrderCancelForm(forms.Form):
    reason = forms.ChoiceField(
        choices=[
            ('changed_mind', 'Передумал'),
            ('found_cheaper', 'Нашел дешевле'),
            ('wrong_address', 'Неправильный адрес'),
            ('long_delivery', 'Долгая доставка'),
            ('other', 'Другая причина')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Причина отмены'
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Дополнительный комментарий (необязательно)'
        }),
        required=False,
        label='Комментарий'
    )