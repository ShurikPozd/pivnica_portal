from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Category, Dish, Event, Customer, Reservation, PaperMenu
from .forms import ReservationForm
import datetime
from datetime import timedelta
from ml.recommender import DishRecommender

def recommend_dishes(request, customer_id=None):
    """
    API для получения рекомендаций блюд.
    """
    try:
        # Загружаем модель
        recommender = DishRecommender.load('ml/models/recommender.pkl')
        
        # Если передан customer_id — ищем его историю
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
                # Получаем последнее бронирование клиента
                last_reservation = Reservation.objects.filter(customer=customer).last()
                if last_reservation:
                    # TODO: связать бронирование с блюдами
                    pass
            except Customer.DoesNotExist:
                return JsonResponse({'error': 'Клиент не найден'}, status=404)
        
        # Берём случайное блюдо для демонстрации
        import random
        dishes = Dish.objects.filter(is_available=True)
        if not dishes:
            return JsonResponse({'error': 'Нет доступных блюд'}, status=404)
        
        random_dish = random.choice(dishes)
        recommendations = recommender.recommend(random_dish.id, n=5)
        
        return JsonResponse({
            'success': True,
            'based_on': random_dish.name,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_popular_dishes(request):
    """
    API для получения популярных блюд.
    """
    # Простая заглушка: возвращаем случайные блюда
    import random
    dishes = Dish.objects.filter(is_available=True)
    popular = random.sample(list(dishes), min(5, len(dishes)))
    
    data = [{
        'id': d.id,
        'name': d.name,
        'price': float(d.price),
    } for d in popular]
    
    return JsonResponse({'popular': data})

def index(request):
    events = Event.objects.filter(is_active=True, event_date__gte=datetime.date.today()).order_by('event_date')[:3]
    return render(request, 'portal/index.html', {'events': events})

def menu(request):
    categories = Category.objects.all()
    dishes = Dish.objects.filter(is_available=True)
    return render(request, 'portal/menu.html', {'categories': categories, 'dishes': dishes})

def event_list(request):
    events = Event.objects.filter(is_active=True, event_date__gte=datetime.date.today()).order_by('event_date')
    return render(request, 'portal/events.html', {'events': events})

def reservation_create(request):
    event_id = request.GET.get('event')
    initial = {}
    selected_event = None
    if event_id:
        try:
            selected_event = Event.objects.get(pk=event_id)
            initial['event'] = selected_event
            initial['reservation_date'] = selected_event.event_date
        except Event.DoesNotExist:
            pass

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            selected_event = form.cleaned_data.get('event')
            phone = form.cleaned_data['phone']
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                defaults={'name': form.cleaned_data['name'], 'email': form.cleaned_data.get('email', '')}
            )
            if not created and customer.name != form.cleaned_data['name']:
                customer.name = form.cleaned_data['name']
                customer.save()

            if selected_event:
                reservation_date = selected_event.event_date
            else:
                reservation_date = form.cleaned_data['reservation_date']

            reservation = Reservation(
                customer=customer,
                event=selected_event,
                reservation_date=reservation_date,
                reservation_time=form.cleaned_data['reservation_time'],
                guests_count=form.cleaned_data['guests_count'],
                comment=form.cleaned_data.get('comment', '')
            )
            reservation.save()
            messages.success(request, 'Ваша бронь принята! Мы свяжемся с вами для подтверждения.')
            return redirect('portal:reservation_success')
    else:
        form = ReservationForm(initial=initial)
        if event_id:
            form.fields['reservation_date'].widget.attrs['readonly'] = 'readonly'
            form.fields['event'].widget.attrs['disabled'] = 'disabled'

    return render(request, 'portal/reservation_form.html', {'form': form, 'selected_event': selected_event})

def reservation_success(request):
    return render(request, 'portal/reservation_success.html')

def event_date(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        return JsonResponse({'date': event.event_date.isoformat()})
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Мероприятие не найдено'}, status=404)

def event_times(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        return JsonResponse({
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Мероприятие не найдено'}, status=404)

def event_time_slots(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        start = datetime.datetime.combine(datetime.date.today(), event.start_time)
        end = datetime.datetime.combine(datetime.date.today(), event.end_time) - timedelta(hours=1)
        slots = []
        current = start
        while current <= end:
            slots.append(current.strftime('%H:%M'))
            current += timedelta(minutes=30)
        return JsonResponse({'slots': slots, 'default': slots[0] if slots else None})
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Мероприятие не найдено'}, status=404)
    
def paper_menu(request):
    pages = PaperMenu.objects.all()
    return render(request, 'portal/paper_menu.html', {'pages': pages})

def event_detail_api(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        return JsonResponse({
            'name': event.name,
            'description': event.description,
            'event_date': event.event_date.isoformat(),
            'start_time': event.start_time.isoformat(),
            'end_time': event.end_time.isoformat(),
            'image_url': event.image.url if event.image else '',
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Мероприятие не найдено'}, status=404)