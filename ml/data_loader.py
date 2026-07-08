import os
import django
import pandas as pd
from datetime import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pivnica.settings')
django.setup()

from portal.models import Customer, Reservation, Dish, Event, Category


def load_data_to_csv():
    """Загружает данные из Django в CSV-файлы."""
    
    # Создаём папку для данных
    os.makedirs('ml/data', exist_ok=True)
    
    # 1. Клиенты
    customers = Customer.objects.all().values('id', 'name', 'phone', 'bonuses', 'created_at')
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv('ml/data/customers.csv', index=False)
    print(f"✅ Клиенты: {len(df_customers)} записей")
    
    # 2. Блюда
    dishes = Dish.objects.all().values('id', 'name', 'category_id', 'price', 'weight', 'is_available')
    df_dishes = pd.DataFrame(dishes)
    df_dishes.to_csv('ml/data/dishes.csv', index=False)
    print(f"✅ Блюда: {len(df_dishes)} записей")
    
    # 3. Категории
    categories = Category.objects.all().values('id', 'name')
    df_categories = pd.DataFrame(categories)
    df_categories.to_csv('ml/data/categories.csv', index=False)
    print(f"✅ Категории: {len(df_categories)} записей")
    
    # 4. Мероприятия
    events = Event.objects.all().values('id', 'name', 'event_date', 'is_active')
    df_events = pd.DataFrame(events)
    df_events.to_csv('ml/data/events.csv', index=False)
    print(f"✅ Мероприятия: {len(df_events)} записей")
    
    # 5. Бронирования (история заказов)
    reservations = Reservation.objects.all().values(
        'id', 'customer_id', 'event_id', 'reservation_date', 'guests_count', 'status'
    )
    df_reservations = pd.DataFrame(reservations)
    df_reservations.to_csv('ml/data/reservations.csv', index=False)
    print(f"✅ Бронирования: {len(df_reservations)} записей")
    
    print("\n🎉 Данные загружены в папку ml/data/")
    return {
        'customers': df_customers,
        'dishes': df_dishes,
        'categories': df_categories,
        'events': df_events,
        'reservations': df_reservations
    }


if __name__ == '__main__':
    load_data_to_csv()