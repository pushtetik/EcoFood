from django.db import models
from django.utils import timezone
from django.conf import settings

class Review(models.Model):
    # Основная информация
    author_name = models.CharField(
        max_length=100, 
        verbose_name='Имя автора'
    )
    title = models.CharField(
        max_length=200, 
        verbose_name='Заголовок отзыва'
    )
    
    # Связь с пользователем
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )
    
    # Остальные поля остаются без изменений...
    QUALITY_CHOICES = [
        (5, 'Отличное'),
        (4, 'Хорошее'),
        (3, 'Удовлетворительное'),
        (2, 'Плохое'),
        (1, 'Очень плохое'),
    ]
    
    FRESHNESS_CHOICES = [
        (5, 'Максимальная свежесть'),
        (4, 'Очень свежие'),
        (3, 'Средняя свежесть'),
        (2, 'Не очень свежие'),
        (1, 'Несвежие'),
    ]
    
    SERVICE_CHOICES = [
        (5, 'Идеальный сервис'),
        (4, 'Очень хороший'),
        (3, 'Нормальный'),
        (2, 'Плохой'),
        (1, 'Очень плохой'),
    ]
    
    RECOMMEND_CHOICES = [
        (5, 'Определенно да'),
        (4, 'Вероятно да'),
        (3, 'Не уверен(а)'),
        (2, 'Вероятно нет'),
        (1, 'Определенно нет'),
    ]
    
    # Поля опросника
    product_quality = models.IntegerField(
        choices=QUALITY_CHOICES,
        verbose_name='Качество продуктов',
        default=3
    )
    product_freshness = models.IntegerField(
        choices=FRESHNESS_CHOICES,
        verbose_name='Свежесть продуктов',
        default=3
    )
    service_quality = models.IntegerField(
        choices=SERVICE_CHOICES,
        verbose_name='Качество обслуживания',
        default=3
    )
    recommend = models.IntegerField(
        choices=RECOMMEND_CHOICES,
        verbose_name='Рекомендация друзьям',
        default=3
    )
    
    # Рассчитанный общий рейтинг
    calculated_rating = models.FloatField(
        default=0,
        verbose_name='Общая оценка'
    )
    
    comment = models.TextField(
        max_length=500,
        verbose_name='Ваши впечатления',
        blank=True,
        default=''
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Автоматически рассчитываем общий рейтинг
        total = (self.product_quality + self.product_freshness + 
                self.service_quality + self.recommend)
        self.calculated_rating = round(total / 4, 1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Отзыв от {self.author_name} - {self.calculated_rating}/5"