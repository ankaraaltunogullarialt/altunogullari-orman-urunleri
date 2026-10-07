# fabrika/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
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
    
    # ===== İHALELER (AKTİF) =====
    aktif_ihaleler = Ihale.objects.filter(durum='devam_ediyor')
    toplam_ihale_miktar = aktif_ihaleler.aggregate(toplam=Sum('toplam_ihale_miktari'))['toplam'] or 0
    toplam_kalan_miktar = aktif_ihaleler.aggregate(toplam=Sum('kalan_miktar'))['toplam'] or 0
    
    # ===== YENİ KPI'LAR =====
    
    # 1. TÜM İHALELERİN toplam miktarı
    toplam_miktar = Ihale.objects.aggregate(
        toplam=Sum('toplam_ihale_miktari')
    )['toplam'] or 0
    
    # 2. DEVAM EDEN PARTİLERİN toplam miktarı (sadece durum='devam_ediyor')
    devam_eden_miktar = Ihale.objects.filter(
        durum='devam_ediyor'
    ).aggregate(
        toplam=Sum('toplam_ihale_miktari')
    )['toplam'] or 0
    
    # 3. DEVAM EDEN İHALELERİN (KİK BAZLI) toplam miktarı
    # Mantık: Bir KİK altında en az 1 parti devam ediyorsa → KİK'in TÜM partileri devam eden
    devam_eden_kikler = set(Ihale.objects.filter(
        durum='devam_ediyor'
    ).exclude(
        kik_no__isnull=True
    ).exclude(
        kik_no=''
    ).values_list('kik_no', flat=True))
    
    devam_eden_kik_miktar = Ihale.objects.filter(
        kik_no__in=devam_eden_kikler
    ).aggregate(
        toplam=Sum('toplam_ihale_miktari')
    )['toplam'] or 0
    
    # KİK'siz devam eden ihaleler (nadir durum)
    kik_siz_devam = Ihale.objects.filter(
        durum='devam_ediyor',
        kik_no__isnull=True
    )
    devam_eden_kik_miktar += kik_siz_devam.aggregate(
        toplam=Sum('toplam_ihale_miktari')
    )['toplam'] or 0
    
    # Tüm ihalelerin kalan miktarı
    toplam_kalan = Ihale.objects.aggregate(
        toplam=Sum('kalan_miktar')
    )['toplam'] or 0
    
    # Devam eden ihalelerin kalan miktarı
    devam_eden_kalan = aktif_ihaleler.aggregate(
        toplam=Sum('kalan_miktar')
    )['toplam'] or 0
    
    aktif_ihale_sayisi = aktif_ihaleler.count()
    
    kritik_ihale_stok = Ihale.objects.filter(
        kalan_miktar__lt=10,
        kalan_miktar__gt=0,
        durum='devam_ediyor'
    ).count()
    
    # ===== SON EKLENEN ÜRÜNLER =====
    son_urunler = Urun.objects.all().order_by('-gelis_tarihi')[:5]
    
    # ===== ÜRÜN TİPİ DAĞILIMI (Pie Chart için) =====
    tip_dagilimi = Urun.objects.values('urun_tipi').annotate(
        adet=Count('id'),
        miktar=Sum('mevcut_miktar')
    )
    
    # ===== AYLIK SİPARİŞ (Bar Chart için) - TÜRKÇE AY İSİMLERİ =====
    aylar_tr = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }

    son_6_ay = []
    siparis_verileri = []

    for i in range(5, -1, -1):
        ay = timezone.now() - timedelta(days=30*i)
        ay_adi = aylar_tr[ay.month]
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
        # ===== ESKİ DEĞİŞKENLER =====
        'total_urun': total_urun,
        'total_personel': total_personel,
        'total_siparis': total_siparis,
        'total_musteri': total_musteri,
        'toplam_stok': toplam_stok,
        'tukenen': tukenen,
        'kritik_stok': kritik_stok,
        
        # ===== YENİ KPI'LAR =====
        'toplam_miktar': toplam_miktar,
        'toplam_kalan': toplam_kalan,
        'devam_eden_kik_miktar': devam_eden_kik_miktar,
        'devam_eden_miktar': devam_eden_miktar,      # ← YENİ
        'devam_eden_kalan': devam_eden_kalan,        # ← YENİ
        'aktif_ihale_sayisi': aktif_ihale_sayisi,
        'kritik_ihale_stok': kritik_ihale_stok,
        
        # ===== DİĞER =====
        'bugun_giris': bugun_giris,
        'bugun_cikis': bugun_cikis,
        'son_hareketler': son_hareketler,
        'toplam_alacak': toplam_alacak,
        'toplam_borc': toplam_borc,
        'net_bakiye': net_bakiye,
        'aktif_ihaleler': aktif_ihaleler,
        'toplam_ihale_miktar': toplam_ihale_miktar,
        'toplam_kalan_miktar': toplam_kalan_miktar,
        'son_urunler': son_urunler,
        'tip_dagilimi': tip_dagilimi,
        'son_6_ay': son_6_ay,
        'siparis_verileri': siparis_verileri,
    }
    return render(request, 'dashboard.html', context)


# ===== ESKİ URL'LERİ YÖNLENDİR =====
def redirect_ihaleparti(request):
    """Eski /admin/stok/ihaleparti/ URL'ini yönlendir"""
    return redirect('/admin/stok/ihalesevk/')


urlpatterns = [
    # ===== ESKİ URL YÖNLENDİRMESİ =====
    path('admin/stok/ihaleparti/', redirect_ihaleparti),
    path('admin/stok/ihaleparti/<path:path>/', redirect_ihaleparti),
    
    # ===== ANA URL'LER =====
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('stok/', include('stok.urls')),
    path('personel/', include('personel.urls')),
    path('siparis/', include('siparis.urls')),
    path('finans/', include('finans.urls')),
]