# stok/urls.py
from django.urls import path
from . import views

app_name = 'stok'

urlpatterns = [
    # Raporlama
    path('rapor/dashboard/', views.rapor_dashboard, name='rapor_dashboard'),
    path('rapor/stok/', views.stok_raporu, name='stok_raporu'),
    path('rapor/uretim/', views.uretim_raporu, name='uretim_raporu'),
    path('rapor/finans/', views.finans_raporu, name='finans_raporu'),
    path('rapor/ihale/', views.ihale_raporu, name='ihale_raporu'),
    path('rapor/ihale/icmal/', views.ihale_icmal_raporu, name='ihale_icmal_raporu'),
    path('rapor/stok-hareket/', views.stok_hareket_raporu, name='stok_hareket_raporu'),
    # ===== İHALE RAPORLARI =====
    path('rapor/ihale-genel/', views.ihale_genel_raporu, name='ihale_genel_raporu'),
    path('rapor/ihale-kik-icmal/', views.ihale_kik_icmal_raporu, name='ihale_kik_icmal_raporu'),
    path('rapor/ihale-boy-analiz/', views.ihale_boy_analiz_raporu, name='ihale_boy_analiz_raporu'),
    path('rapor/ihale/<int:ihale_id>/', views.ihale_detay_raporu, name='ihale_detay_raporu'),
    # ===== TAŞIYICI RAPORU =====
    path('rapor/tasiyici/', views.tasiyici_raporu, name='tasiyici_raporu'),
    # ===== ÜRÜN ANALİZ RAPORU =====
    path('rapor/ihale-urun-analiz/', views.ihale_urun_analiz_raporu, name='ihale_urun_analiz_raporu'),
    # =====FİİLİ STOK TAKİP RAPORU =====
    path('rapor/fiili-stok/', views.fiili_stok_takip_raporu, name='fiili_stok_takip_raporu'),
    # ===== VERİTABANI YEDEKLEME =====
    path('yedekleme/', views.yedekleme_sayfasi, name='yedekleme_sayfasi'),
    path('yedekleme/olustur/', views.yedek_olustur, name='yedek_olustur'),
    path('yedekleme/indir/<str:yedek_adi>/', views.yedek_indir, name='yedek_indir'),
    path('yedekleme/sil/<str:yedek_adi>/', views.yedek_sil, name='yedek_sil'),
    path('yedekleme/yukle/', views.yedek_yukle, name='yedek_yukle'),
    path('yedekleme/temizle/', views.yedek_temizle, name='yedek_temizle'),
    
    # JSON verileri
    path('grafik/verileri/', views.grafik_verileri, name='grafik_verileri'),
    
    # Analiz
    path('analiz/hareket/', views.hareket_analizi, name='hareket_analizi'),
    path('analiz/uretim/', views.uretim_analizi, name='uretim_analizi'),
]