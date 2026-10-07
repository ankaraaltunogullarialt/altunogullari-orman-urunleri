# siparis/urls.py
from django.urls import path
from . import views

app_name = 'siparis'

urlpatterns = [
    path('satis-raporu/', views.satis_raporu, name='satis_raporu'),
]