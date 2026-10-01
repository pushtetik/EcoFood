from django.urls import path
from . import views

app_name = 'catalog'  

urlpatterns = [
    path('', views.catalog, name='catalog'),  
    path('<int:product_id>/', views.product_detail, name='product_detail'),  
    path('cart/', views.cart, name='cart'), 
]