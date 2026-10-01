from django.contrib import admin
from django.urls import path, include  
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from catalog.models import Product

def home_view(request):
    print("=" * 50)
    print("ГЛАВНАЯ СТРАНИЦА ВЫЗВАНА")
    
    products = Product.objects.all()[:4]
    print(f"Товаров: {products.count()}")
    
    popular_products = [
        {
            'product': product,
            'total_quantity': 42,
            'total_orders': 10
        }
        for product in products
    ]
    
    print("=" * 50)
    
    return render(request, 'index.html', {
        'popular_products': popular_products
    })

urlpatterns = [
    path('admin/', admin.site.urls),
path('', include('homepage.urls')),  
    path('cart/', include('cart.urls')),
    path('catalog/', include('catalog.urls')),  
    path('about/', include('about.urls')), 
    path('delivery/', include('delivery.urls')),  
    path('contacts/', include('contacts.urls')), 
    path('reviews/', include('reviews.urls')),  
    path('users/', include('users.urls')),
    path('orders/', include('orders.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)