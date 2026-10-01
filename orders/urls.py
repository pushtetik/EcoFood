from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('create/', views.create_order_from_modal, name='order_create'), 
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('promocode/apply/', views.apply_promocode, name='apply_promocode'),
    path('promocode/remove/', views.remove_promocode, name='remove_promocode'),
]