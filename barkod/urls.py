# barkod/urls.py
from django.urls import path
from . import views

app_name = 'barkod'

urlpatterns = [
    # Dashboard
    path('', views.barkod_dashboard, name='dashboard'),
    
    # Sevk listesi
    path('sevk-listesi/', views.sevk_listesi, name='sevk_listesi'),
    
    # Teslim alma
    path('teslim-al/<int:sevkiyat_id>/', views.teslim_al, name='teslim_al'),
    path('teslim-al/kaydet/', views.teslim_al_kaydet, name='teslim_al_kaydet'),
    
    # Barkod yazdırma
    path('yazdir/<int:sevkiyat_id>/', views.barkod_yazdir, name='barkod_yazdir'),
    path('yazdir/<int:sevkiyat_id>/pdf/', views.barkod_yazdir_pdf, name='barkod_yazdir_pdf'),
    
    # Barkod okuma
    path('oku/', views.barkod_oku, name='barkod_oku'),
    path('oku/kaydet/', views.barkod_oku_kaydet, name='barkod_oku_kaydet'),
    
    # Detay
    path('detay/<str:barkod>/', views.barkod_detay, name='barkod_detay'),
    path('gecmis/<str:barkod>/', views.barkod_gecmis, name='barkod_gecmis'),
    
    # Raporlar
    path('rapor/stok/', views.rapor_stok, name='rapor_stok'),
]