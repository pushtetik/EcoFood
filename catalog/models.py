
from django.db import models
from django.core.validators import FileExtensionValidator
class Category(models.Model):
    slug = models.SlugField('Slug', max_length=50, unique=True)
    name = models.CharField('Название', max_length=100)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']
    
    def __str__(self):
        return self.name
class Product(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='Категория',
        related_name='products'
    )
    
    old_price = models.DecimalField(
        'Старая цена', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    image_url = models.URLField(
        'Ссылка на изображение', 
        max_length=500,
        blank=True,
        default='',
        help_text='Или используйте ссылку на изображение'
    )
    
    image_file = models.ImageField(
        'Загруженное изображение',
        upload_to='products/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp','jfif']
        )],
        help_text='Загрузите изображение с компьютера'
    )
    
    in_stock = models.BooleanField('В наличии', default=True)
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def category_display(self):
        return self.category.name if self.category else ''
    
    @property
    def image(self):
        """
        Умное свойство для получения изображения.
        Приоритет: загруженный файл > URL > заглушка
        """
        if self.image_file and hasattr(self.image_file, 'url'):
            return self.image_file.url
        elif self.image_url:
            return self.image_url
        else:
            return '/static/images/no-image.jpg'
    
    def save(self, *args, **kwargs):
        if self.image_file and self.image_url:
            self.image_url = ''
        super().save(*args, **kwargs)