from django import forms
from .models import Event

class ReservationForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.filter(is_active=True), required=False, label='Мероприятие')
    reservation_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Дата')
    reservation_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label='Время')
    guests_count = forms.IntegerField(min_value=1, max_value=20, label='Количество гостей')
    name = forms.CharField(max_length=100, label='Ваше имя')
    phone = forms.CharField(max_length=20, label='Телефон')
    email = forms.EmailField(required=False, label='Email')
    comment = forms.CharField(widget=forms.Textarea, required=False, label='Комментарий')