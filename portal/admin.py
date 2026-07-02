from django.contrib import admin
from .models import Category, Dish, Event, Customer, Reservation
from .models import PaperMenu

admin.site.register(Category)
admin.site.register(Dish)
admin.site.register(Event)
admin.site.register(Customer)
admin.site.register(Reservation)
admin.site.register(PaperMenu)