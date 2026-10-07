# fabrika/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from stok.models import Urun, Ihale, StokHareket
from personel.models import Personel
from siparis.models import Siparis, Musteri
from finans.models import CariHesap, Banka

def dashboard(request):
    """Gelişmiş Dashboard"""
    # ===== TEMEL İSTATİSTİKLER =====
    total_urun = Urun.objects.count()
    total_personel = Personel.objects.filter(calisma_durumu='aktif').count()
    total_siparis = Siparis.objects.count()
    total_musteri = Musteri.objects.count()
    
    # ===== STOK DURUMU =====
    kritik_stok = Urun.objects.filter(mevcut_miktar__lt=10, stokta_mi=True)
    toplam_stok = Urun.objects.aggregate(toplam=Sum('mevcut_miktar'))['toplam'] or 0
    tukenen = Urun.objects.filter(mevcut_miktar=0).count()
    
    # ===== BUGÜNKÜ HAREKETLER =====
    bugun = timezone.now().date()
    bugun_hareketler = StokHareket.objects.filter(tarih__date=bugun)
    bugun_giris = bugun_hareketler.filter(hareket_tipi__in=['ihale_giris', 'sahis_alim', 'mamul_giris']).aggregate(toplam=Sum('miktar'))['toplam'] or 0
    bugun_cikis = bugun_hareketler.filter(hareket_tipi__in=['siparis_cikis', 'hammadde_cikis']).aggregate(toplam=Sum('miktar'))['toplam'] or 0
    
    # ===== SON 7 GÜN HAREKETLER =====
    son_7_gun = timezone.now() - timedelta(days=7)
    son_hareketler = StokHareket.objects.filter(tarih__gte=son_7_gun).order_by('-tarih')[:10]
    
    # ===== FİNANS =====
    toplam_alacak = CariHesap.objects.aggregate(toplam=Sum('alacak'))['toplam'] or 0
    toplam_borc = CariHesap.objects.aggregate(toplam=Sum('borc'))['toplam'] or 0
    net_bakiye = toplam_alacak - toplam_borc
    
    # ===== İHALELER =====
    aktif_ihaleler = Ihale.objects.filter(durum='devam_ediyor')
    toplam_ihale_miktar = aktif_ihaleler.aggregate(toplam=Sum('toplam_miktar'))['toplam'] or 0
    
    # ===== SON EKLENEN ÜRÜNLER =====
    son_urunler = Urun.objects.all().order_by('-gelis_tarihi')[:5]
    
    # ===== ÜRÜN TİPİ DAĞILIMI (Pie Chart için) =====
    tip_dagilimi = Urun.objects.values('urun_tipi').annotate(
        adet=Count('id'),
        miktar=Sum('mevcut_miktar')
    )
    
    # ===== AYLIK SİPARİŞ (Bar Chart için) - TÜRKÇE AY İSİMLERİ =====
    # Türkçe ay isimleri sözlüğü
    aylar_tr = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }

    son_6_ay = []
    siparis_verileri = []

    for i in range(5, -1, -1):
        ay = timezone.now() - timedelta(days=30*i)
        ay_adi = aylar_tr[ay.month]  # Türkçe ay adı
        son_6_ay.append(ay_adi)
        
        ay_baslangic = ay.replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            ay_bitis = timezone.now()
        else:
            sonraki_ay = ay + timedelta(days=32)
            ay_bitis = sonraki_ay.replace(day=1, hour=0, minute=0, second=0) - timedelta(seconds=1)
        
        siparis_sayisi = Siparis.objects.filter(
            siparis_tarihi__range=(ay_baslangic, ay_bitis)
        ).count()
        siparis_verileri.append(siparis_sayisi)
    
    context = {
        # Temel
        'total_urun': total_urun,
        'total_personel': total_personel,
        'total_siparis': total_siparis,
        'total_musteri': total_musteri,
        'toplam_stok': toplam_stok,
        'tukenen': tukenen,
        
        # Stok
        'kritik_stok': kritik_stok,
        'bugun_giris': bugun_giris,
        'bugun_cikis': bugun_cikis,
        'son_hareketler': son_hareketler,
        
        # Finans
        'toplam_alacak': toplam_alacak,
        'toplam_borc': toplam_borc,
        'net_bakiye': net_bakiye,
        
        # İhale
        'aktif_ihaleler': aktif_ihaleler,
        'toplam_ihale_miktar': toplam_ihale_miktar,
        
        # Son ürünler
        'son_urunler': son_urunler,
        
        # Grafik verileri
        'tip_dagilimi': tip_dagilimi,
        'son_6_ay': son_6_ay,
        'siparis_verileri': siparis_verileri,
    }
    return render(request, 'dashboard.html', context)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('stok/', include('stok.urls')),
    path('personel/', include('personel.urls')),
    path('siparis/', include('siparis.urls')),  # BURASI ÖNEMLİ!
    path('finans/', include('finans.urls')),
]