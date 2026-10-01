from django.shortcuts import render

def cart_page(request):
    """Страница корзины"""
    context = {
        'title': 'Корзина',
        'cart_total_quantity': 0,  
    }
    return render(request, 'cart_page.html', context)