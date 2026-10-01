from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+7 (999) 999-99-99'
        }),
        help_text="Будет использоваться для входа в аккаунт"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'your@email.com'
        }),
        help_text="Будет использоваться для восстановления пароля"
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Ваше имя'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 
            'type': 'date'
        })
    )

    class Meta:
        model = User
        fields = ('phone', 'email', 'first_name', 'date_of_birth', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем классы Bootstrap ко всем полям
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
            
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email
        
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже существует.")
        return phone


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '+7 (999) 999-99-99'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Телефон'
    
    def clean(self):
        phone = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if phone and password:
            try:
                user = User.objects.get(phone=phone)
                # Проверяем пароль
                if user.check_password(password):
                    self.user_cache = user
                    return self.cleaned_data
                else:
                    raise forms.ValidationError("Неверный телефон или пароль.")
            except User.DoesNotExist:
                raise forms.ValidationError("Неверный телефон или пароль.")
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone', 'email', 'first_name', 'date_of_birth']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].help_text = "Основной идентификатор для входа"
        self.fields['email'].help_text = "Для восстановления пароля"