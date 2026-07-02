from django.urls import path
from . import views

app_name = 'portal'
urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('events/', views.event_list, name='events'),
    path('reservation/', views.reservation_create, name='reservation'),
    path('reservation/success/', views.reservation_success, name='reservation_success'),
    path('api/event-date/<int:event_id>/', views.event_date, name='event_date'),
    path('api/event-times/<int:event_id>/', views.event_times, name='event_times'),
    path('paper-menu/', views.paper_menu, name='paper_menu'),
    path('api/event-detail/<int:event_id>/', views.event_detail_api, name='event_detail_api'),
]