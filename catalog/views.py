from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def catalog(request):
    categories = Category.objects.all()
    products = Product.objects.select_related('category').all()
    if not products.exists():
        create_initial_data()
        products = Product.objects.select_related('category').all()
        categories = Category.objects.all()
    
    return render(request, 'catalog.html', {
        'products': products,
        'categories': categories,  
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def cart(request):
    return render(request, 'cart.html')

def create_initial_data():
    """Создает начальные данные если база пустая"""
    categories_data = [
        ('vegetables', 'Овощи'),
        ('fruits', 'Фрукты'),
        ('dairy', 'Молочные продукты'),
        ('meat', 'Мясо и птица'),
    ]
    
    category_map = {}
    for slug, name in categories_data:
        cat, created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name}
        )
        category_map[slug] = cat
    
    products_data = [
        
    ]
    
    for data in products_data:
        if not Product.objects.filter(name=data['name']).exists():
            Product.objects.create(
                name=data['name'],
                description=data['description'],
                price=data['price'],
                old_price=data['old_price'],
                image_url=data['image_url'],
                in_stock=data['in_stock'],
                category=category_map[data['category_slug']]
            )