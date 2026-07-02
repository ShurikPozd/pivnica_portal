from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок')

    class Meta:
        ordering = ['sort_order']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

class Dish(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    ingredients = models.TextField(verbose_name='Состав')
    weight = models.IntegerField(verbose_name='Вес (г)', validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Цена (руб.)')
    is_available = models.BooleanField(default=True, verbose_name='Доступно')
    image = models.ImageField(upload_to='dishes/', blank=True, null=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

    def __str__(self):
        return f'{self.name} - {self.price} руб.'

class Event(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    event_date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Начало')
    end_time = models.TimeField(verbose_name='Окончание')
    special_menu = models.TextField(blank=True, verbose_name='Специальное меню')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    image = models.ImageField(upload_to='events/', blank=True, null=True, verbose_name='Фото')

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return f'{self.name} ({self.event_date})'

class Customer(models.Model):
    name = models.CharField(max_length=100, verbose_name='Имя')
    phone = models.CharField(max_length=20, unique=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    bonuses = models.IntegerField(default=0, verbose_name='Бонусы')

    def __str__(self):
        return f'{self.name} ({self.phone})'

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Выполнено'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент')
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Мероприятие')
    reservation_date = models.DateField(verbose_name='Дата брони')
    reservation_time = models.TimeField(verbose_name='Время')
    guests_count = models.IntegerField(verbose_name='Количество гостей', validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-reservation_date', '-reservation_time']

    def __str__(self):
        return f'{self.customer.name} - {self.reservation_date} {self.reservation_time}'
    
class PaperMenu(models.Model):
    title = models.CharField(max_length=100, verbose_name="Название страницы", blank=True)
    image = models.ImageField(upload_to='paper_menu/', verbose_name="Изображение страницы меню")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        ordering = ['order']
        verbose_name = "Страница бумажного меню"
        verbose_name_plural = "Страницы бумажного меню"

    def __str__(self):
        return self.title or f"Страница {self.order}"