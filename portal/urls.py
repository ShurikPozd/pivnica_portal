from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('events/', views.event_list, name='events'),
    path('paper-menu/', views.paper_menu, name='paper_menu'),
    
    # Бронирование
    path('reservation/', views.reservation_create, name='reservation'),
    path('reservation/success/', views.reservation_success, name='reservation_success'),
    
    # Авторизация
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # API
    path('api/event-date/<int:event_id>/', views.event_date, name='event_date'),
    path('api/event-times/<int:event_id>/', views.event_times, name='event_times'),
    path('api/event-detail/<int:event_id>/', views.event_detail_api, name='event_detail_api'),
    
    # API - ML рекомендации
    path('api/recommend/', views.recommend_dishes, name='recommend'),
    path('api/recommend/<int:customer_id>/', views.recommend_dishes, name='recommend_for_customer'),
    path('api/recommend/season/', views.recommend_by_season, name='recommend_season'),
    path('api/recommend/customer/<int:customer_id>/', views.recommend_for_customer, name='recommend_customer'),
    path('api/popular/', views.get_popular_dishes, name='popular'),
]