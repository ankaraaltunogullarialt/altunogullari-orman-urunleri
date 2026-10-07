# personel/urls.py
from django.urls import path
from . import views

app_name = 'personel'

urlpatterns = [
    path('rapor/', views.personel_raporu, name='personel_raporu'),
]