from django.contrib import admin
from .models import Category, Dish, Event, Customer, Reservation, PaperMenu, Order, OrderItem, SiteSettings

admin.site.register(Category)
admin.site.register(Dish)
admin.site.register(Event)
admin.site.register(Customer)
admin.site.register(Reservation)
admin.site.register(PaperMenu)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'created_at', 'total_amount']
    list_filter = ['created_at']
    search_fields = ['customer__name', 'customer__phone']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'dish', 'quantity', 'price']
    list_filter = ['order__created_at']
    search_fields = ['dish__name']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['recommendations_count', 'updated_at']
    readonly_fields = ['updated_at']
    fields = ['recommendations_count', 'updated_at']