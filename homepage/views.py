
from django.shortcuts import render
from django.db.models import Sum, Count
from catalog.models import Product
from orders.models import OrderItem

def index(request):
   

    stats = OrderItem.objects.filter(
        order__status='delivered'
    ).values(
        'product_id'  
    ).annotate(
        total_quantity=Sum('quantity'),
        total_orders=Count('order_id', distinct=True)
    ).order_by(
        '-total_quantity'
    )[:4] 
    
  
    product_ids = [stat['product_id'] for stat in stats]
    
  
    products_dict = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    
 
    popular_products = []
    
    for stat in stats:
        product_id = stat['product_id']
        product = products_dict.get(product_id)
        
        if product:
            popular_products.append({
                'product': product,
                'total_quantity': stat['total_quantity'] or 0,
                'total_orders': stat['total_orders'] or 0
            })
       
    return render(request, 'index.html', {
        'popular_products': popular_products
    })