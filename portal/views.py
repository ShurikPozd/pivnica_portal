from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Category, Dish, Event, Customer, Reservation, PaperMenu, Order, OrderItem, SiteSettings
from .forms import ReservationForm
import datetime
from datetime import timedelta
import random


# ============================================================
# АВТОРИЗАЦИЯ
# ============================================================

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if not username:
            messages.error(request, 'Имя пользователя обязательно')
            return render(request, 'portal/register.html')
        
        if not email:
            messages.error(request, 'Email обязателен')
            return render(request, 'portal/register.html')
        
        if not phone:
            messages.error(request, 'Телефон обязателен')
            return render(request, 'portal/register.html')
        
        if not password1 or not password2:
            messages.error(request, 'Пароль обязателен')
            return render(request, 'portal/register.html')
        
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'portal/register.html')
        
        if len(password1) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
            return render(request, 'portal/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return render(request, 'portal/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, 'portal/register.html')
        
        if Customer.objects.filter(phone=phone).exists():
            messages.error(request, 'Пользователь с таким телефоном уже зарегистрирован')
            return render(request, 'portal/register.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            
            customer = Customer.objects.create(
                user=user,
                name=username,
                phone=phone,
                email=email,
                bonuses=100
            )
            
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}! Вам начислено 100 бонусов.')
            return redirect('portal:index')
            
        except Exception as e:
            messages.error(request, f'Ошибка при регистрации: {str(e)}')
            return render(request, 'portal/register.html')
    
    return render(request, 'portal/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('portal:index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'portal/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('portal:index')


@login_required
def profile(request):
    customer, created = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.username,
            'phone': None,
            'email': request.user.email,
            'bonuses': 0
        }
    )
    if created:
        customer.bonuses = 100
        customer.save()
    
    reservations = Reservation.objects.filter(customer=customer).order_by('-reservation_date')
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    return render(request, 'portal/profile.html', {
        'customer': customer,
        'reservations': reservations,
        'orders': orders,
    })


@login_required
def profile_edit(request):
    customer = request.user.customer
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        if name:
            customer.name = name
        if email:
            customer.email = email
        if phone:
            customer.phone = phone
        
        customer.save()
        messages.success(request, 'Профиль успешно обновлён!')
        return redirect('portal:profile')
    
    return render(request, 'portal/profile_edit.html', {'customer': customer})


# ============================================================
# ОСНОВНЫЕ СТРАНИЦЫ
# ============================================================

def index(request):
    events = Event.objects.filter(is_active=True, event_date__gte=datetime.date.today()).order_by('event_date')[:3]
    return render(request, 'portal/index.html', {'events': events})


def menu(request):
    categories = Category.objects.all()
    dishes = Dish.objects.filter(is_available=True)
    settings = SiteSettings.objects.first()
    return render(request, 'portal/menu.html', {
        'categories': categories,
        'dishes': dishes,
        'settings': settings
    })


def event_list(request):
    events = Event.objects.filter(is_active=True, event_date__gte=datetime.date.today()).order_by('event_date')
    return render(request, 'portal/events.html', {'events': events})


def paper_menu(request):
    pages = PaperMenu.objects.all()
    return render(request, 'portal/paper_menu.html', {'pages': pages})


# ============================================================
# БРОНИРОВАНИЕ
# ============================================================

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
            
            if hasattr(customer, 'user') and customer.user:
                bonus_points = 50
                customer.bonuses += bonus_points
                customer.save()
                messages.success(request, f'Ваша бронь принята! Вам начислено {bonus_points} бонусов!')
            else:
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


# ============================================================
# API-ЭНДПОИНТЫ
# ============================================================

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


# ============================================================
# ML-РЕКОМЕНДАЦИИ
# ============================================================

from ml.recommender import DishRecommender


def get_limit_from_request(request, default=None):
    """Получает параметр limit из GET-запроса."""
    try:
        limit = int(request.GET.get('limit', default or 0))
        if limit > 0:
            return limit
    except (ValueError, TypeError):
        pass
    
    # Если не передан или некорректен — берём из настроек
    try:
        settings = SiteSettings.objects.first()
        if settings:
            return settings.recommendations_count
    except:
        pass
    
    return default or 5


def recommend_dishes(request, customer_id=None):
    try:
        limit = get_limit_from_request(request, 5)
        recommender = DishRecommender.load('ml/models/recommender.pkl')
        
        if customer_id:
            recommendations = recommender.recommend_for_customer(customer_id, n=limit)
            if recommendations:
                return JsonResponse({
                    'success': True,
                    'limit': limit,
                    'recommendations': recommendations
                })
        
        dishes = Dish.objects.filter(is_available=True)
        if not dishes:
            return JsonResponse({'error': 'Нет доступных блюд'}, status=404)
        
        random_dish = random.choice(dishes)
        recommendations = recommender.recommend(random_dish.id, n=limit)
        
        return JsonResponse({
            'success': True,
            'limit': limit,
            'based_on': random_dish.name,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def recommend_by_season(request):
    try:
        limit = get_limit_from_request(request, 5)
        recommender = DishRecommender.load('ml/models/recommender.pkl')
        result = recommender.recommend_by_season(n=limit)
        result['limit'] = limit
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def recommend_for_customer(request, customer_id):
    try:
        limit = get_limit_from_request(request, 5)
        recommender = DishRecommender.load('ml/models/recommender.pkl')
        recommendations = recommender.recommend_for_customer(customer_id, n=limit)
        return JsonResponse({
            'success': True,
            'limit': limit,
            'recommendations': recommendations
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_popular_dishes(request):
    try:
        limit = get_limit_from_request(request, 5)
        recommender = DishRecommender.load('ml/models/recommender.pkl')
        popular = recommender.recommend_popular(n=limit)
        return JsonResponse({
            'popular': popular,
            'limit': limit
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)