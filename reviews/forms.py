from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            'title', 'product_quality', 
            'product_freshness', 'service_quality', 'recommend', 'comment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Кратко о вашем опыте покупки'
            }),
            'product_quality': forms.HiddenInput(),
            'product_freshness': forms.HiddenInput(),
            'service_quality': forms.HiddenInput(),
            'recommend': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Поделитесь вашими впечатлениями о наших продуктах и сервисе...',
                'rows': 4,
                'maxlength': '500'
            })
        }
        labels = {
            'title': 'Заголовок отзыва *',
            'comment': 'Ваши впечатления'
        }