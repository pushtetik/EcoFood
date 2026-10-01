from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import timedelta
from .forms import CustomUserCreationForm, PhoneAuthenticationForm, ProfileUpdateForm
from orders.models import Order


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    form_class = PhoneAuthenticationForm 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Вход по телефону'
        return context


class RegisterView(View):
    template_name = 'users/register.html'
    
    def get(self, request):
        context = {
            'form': CustomUserCreationForm(),
            'title': 'Регистрация'
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        
        context = {
            'form': form,
            'title': 'Регистрация'
        }
        return render(request, self.template_name, context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    
    user_orders = Order.objects.filter(user=request.user)
    

    orders_count = user_orders.count()
    
   
    completed_orders_count = user_orders.filter(status='delivered').count()
    
   
    if request.user.date_joined:
        days_with_us = (now().date() - request.user.date_joined.date()).days
        days_with_us = max(1, days_with_us)
    else:
        days_with_us = 1
    
    context = {
        'form': form,
        'title': 'Мой профиль',
        'orders_count': orders_count,
        'completed_orders_count': completed_orders_count,
        'days_with_us': days_with_us,
    }
    return render(request, 'users/profile.html', context)


def custom_logout(request):
    logout(request)
    return redirect('index')