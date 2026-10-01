from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Review
from .forms import ReviewForm

def reviews_page(request):
    reviews = Review.objects.all()
    form = None
    
    if request.method == 'POST':
        print("=" * 60)
        print("ПОЛУЧЕН ОПРОС ОТ ПОЛЬЗОВАТЕЛЯ!")
        print("=" * 60)
        
        if not request.user.is_authenticated:
            messages.error(request, 'Для оставления отзыва необходимо войти в систему.')
            return redirect('reviews:reviews')
        
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            
            # Автоматически заполняем имя из профиля пользователя
            review.author_name = request.user.first_name
            
            # Связываем отзыв с пользователем
            review.user = request.user
            
            review.save()
            
            # Выводим данные в консоль
            author_name = request.user.first_name
            title = form.cleaned_data['title']
            product_quality = form.cleaned_data['product_quality']
            product_freshness = form.cleaned_data['product_freshness']
            service_quality = form.cleaned_data['service_quality']
            recommend = form.cleaned_data['recommend']
            comment = form.cleaned_data['comment']
            
            print("ОПРОС СОХРАНЕН В БАЗУ!")
            print(f"Пользователь: {request.user}")
            print(f"Имя: {author_name}")
            print(f"Заголовок: {title}") 
            print(f"Качество продуктов: {product_quality}/5")
            print(f"Свежесть: {product_freshness}/5")
            print(f"Обслуживание: {service_quality}/5")
            print(f"Рекомендация: {recommend}/5")
            print(f"Общая оценка: {review.calculated_rating}/5")
            print(f"Текст: '{comment}'")
            print(f"ID записи: {review.id}")
            print(f"Дата создания: {review.created_at}")
            print("=" * 60)
            
            messages.success(request, f'Спасибо, {author_name}! Ваша оценка "{title}" успешно сохранена!')
            return redirect('reviews:reviews')
        else:
            print("❌ ОШИБКИ В ФОРМЕ ОПРОСА:")
            print(form.errors)
            print("=" * 60)
            
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ReviewForm()

    # Статистика для отображения
    total_reviews = reviews.count()
    
    avg_quality = avg_freshness = avg_service = avg_rating = 0
    recommend_percentage = 0
    quality_percentage = freshness_percentage = service_percentage = 0
    
    if total_reviews > 0:
        # Средние значения по критериям
        avg_quality = sum(review.product_quality for review in reviews) / total_reviews
        avg_freshness = sum(review.product_freshness for review in reviews) / total_reviews
        avg_service = sum(review.service_quality for review in reviews) / total_reviews
        avg_rating = sum(review.calculated_rating for review in reviews) / total_reviews
        
        # Процент рекомендаций (оценки 4-5)
        recommend_reviews = reviews.filter(recommend__gte=4).count()
        recommend_percentage = (recommend_reviews / total_reviews) * 100
        
        # Проценты для визуализации (максимум 5 баллов = 100%)
        quality_percentage = (avg_quality / 5) * 100
        freshness_percentage = (avg_freshness / 5) * 100
        service_percentage = (avg_service / 5) * 100
    
    context = {
        'reviews': reviews,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'recommend_percentage': round(recommend_percentage),
        'avg_quality': round(avg_quality, 1),
        'avg_freshness': round(avg_freshness, 1),
        'avg_service': round(avg_service, 1),
        'quality_percentage': round(quality_percentage),
        'freshness_percentage': round(freshness_percentage),
        'service_percentage': round(service_percentage),
        'form': form,
        'user_is_authenticated': request.user.is_authenticated,
        'user_name': request.user.first_name if request.user.is_authenticated else ''
    }
    
    return render(request, 'reviews.html', context)