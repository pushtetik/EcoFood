from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, phone, email, first_name, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        if not first_name:
            raise ValueError('The First Name field must be set')
            
        email = self.normalize_email(email)
        user = self.model(
            phone=phone,
            email=email,
            first_name=first_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, email, first_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(phone, email, first_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='Телефон'
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name='Email адрес'
    )
    
    first_name = models.CharField(
        max_length=30, 
        verbose_name='Имя',
        blank=False
    )
    

    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Дата рождения'
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['email', 'first_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.first_name} ({self.phone})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'