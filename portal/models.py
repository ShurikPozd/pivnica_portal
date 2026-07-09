from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_migrate  # <--- ДОБАВЛЕНО post_migrate
from django.dispatch import receiver

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
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Пользователь')
    name = models.CharField(max_length=100, verbose_name='Имя')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    bonuses = models.IntegerField(default=0, verbose_name='Бонусы')

    def __str__(self):
        return f'{self.name} ({self.phone or "телефон не указан"})'
    
    def add_bonuses(self, amount):
        self.bonuses += amount
        self.save()
    
    def use_bonuses(self, amount):
        if self.bonuses >= amount:
            self.bonuses -= amount
            self.save()
            return True
        return False


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


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Клиент', related_name='orders')
    reservation = models.OneToOneField(Reservation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Бронирование')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Заказ #{self.id} - {self.customer.name} ({self.total_amount} руб.)'
    
    def update_total(self):
        from django.db.models import Sum
        total = self.items.aggregate(total=Sum('price'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name='Блюдо')
    quantity = models.IntegerField(default=1, verbose_name='Количество', validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    
    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'
    
    def __str__(self):
        return f'{self.dish.name} x{self.quantity} = {self.price * self.quantity} руб.'
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.dish.price
        super().save(*args, **kwargs)
        self.order.update_total()


# ============================================================
# НАСТРОЙКИ САЙТА
# ============================================================

class SiteSettings(models.Model):
    """Глобальные настройки сайта."""
    recommendations_count = models.IntegerField(
        default=5,
        verbose_name='Количество рекомендаций',
        help_text='Сколько блюд показывать в блоке рекомендаций (3-12)',
        validators=[MinValueValidator(3)]
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return f'Настройки (рекомендаций: {self.recommendations_count})'


# ============================================================
# СИГНАЛЫ
# ============================================================

@receiver(post_save, sender=User)
def create_customer_for_user(sender, instance, created, **kwargs):
    if created:
        Customer.objects.get_or_create(
            user=instance,
            defaults={
                'name': instance.username,
                'phone': None,
                'email': instance.email,
                'bonuses': 0
            }
        )


# Создаём настройки по умолчанию при первой миграции
@receiver(post_migrate)
def create_default_settings(sender, **kwargs):
    if sender.name == 'portal':
        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(recommendations_count=5)
            print('✅ Созданы настройки сайта по умолчанию')