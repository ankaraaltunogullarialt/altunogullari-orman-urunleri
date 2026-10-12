# stok/utils.py
from django.db.models import Sum
from datetime import date
from decimal import Decimal


def gunluk_snapshot_olustur(tarih=None):
    """
    Belirtilen tarih için snapshot oluştur.
    tarih=None ise bugün için oluşturur.
    """
    from stok.models import (
        Ihale, Urun, IhaleSevk,
        GunlukSnapshot
    )
    from finans.models import CariHesap, Banka
    from barkod.models import BarkodAdet
    
    if tarih is None:
        tarih = date.today()
    
    # Daha önce bu tarih için snapshot var mı?
    mevcut = GunlukSnapshot.objects.filter(tarih=tarih).first()
    if mevcut:
        return mevcut
    
    # ===== İHALE VERİLERİ =====
    ihaleler = Ihale.objects.filter(alis_tarihi__lte=tarih)
    toplam_ihale = ihaleler.count()
    toplam_ihale_miktari = ihaleler.aggregate(
        toplam=Sum('toplam_ihale_miktari')
    )['toplam'] or Decimal('0')
    toplam_kalan_miktar = ihaleler.aggregate(
        toplam=Sum('kalan_miktar')
    )['toplam'] or Decimal('0')
    toplam_ihale_tutari = ihaleler.aggregate(
        toplam=Sum('toplam_tutar')
    )['toplam'] or Decimal('0')
    
    # ===== STOK VERİLERİ =====
    urunler = Urun.objects.all()
    toplam_urun = urunler.count()
    toplam_stok_miktari = urunler.aggregate(
        toplam=Sum('mevcut_miktar')
    )['toplam'] or Decimal('0')
    kritik_stok_sayisi = urunler.filter(
        mevcut_miktar__lt=10, stokta_mi=True
    ).count()
    
    # ===== SEVK VERİLERİ =====
    sevkler = IhaleSevk.objects.filter(sevk_tarihi__lte=tarih)
    toplam_sevk = sevkler.count()
    toplam_sevk_miktari = sevkler.aggregate(
        toplam=Sum('sevk_miktar')
    )['toplam'] or Decimal('0')
    
    # ===== FİNANS =====
    try:
        toplam_alacak = CariHesap.objects.aggregate(
            toplam=Sum('alacak')
        )['toplam'] or Decimal('0')
        toplam_borc = CariHesap.objects.aggregate(
            toplam=Sum('borc')
        )['toplam'] or Decimal('0')
        toplam_banka = Banka.objects.filter(aktif_mi=True).aggregate(
            toplam=Sum('bakiye')
        )['toplam'] or Decimal('0')
    except Exception:
        toplam_alacak = toplam_borc = toplam_banka = Decimal('0')
    
    # ===== BARKOD =====
    try:
        toplam_barkod = BarkodAdet.objects.count()
        depoda_barkod = BarkodAdet.objects.filter(durum='depoda').count()
    except Exception:
        toplam_barkod = depoda_barkod = 0
    
    # ===== SNAPSHOT OLUŞTUR =====
    snapshot = GunlukSnapshot.objects.create(
        tarih=tarih,
        toplam_ihale=toplam_ihale,
        toplam_ihale_miktari=toplam_ihale_miktari,
        toplam_kalan_miktar=toplam_kalan_miktar,
        toplam_ihale_tutari=toplam_ihale_tutari,
        toplam_urun=toplam_urun,
        toplam_stok_miktari=toplam_stok_miktari,
        kritik_stok_sayisi=kritik_stok_sayisi,
        toplam_sevk=toplam_sevk,
        toplam_sevk_miktari=toplam_sevk_miktari,
        toplam_alacak=toplam_alacak,
        toplam_borc=toplam_borc,
        toplam_banka=toplam_banka,
        toplam_barkod=toplam_barkod,
        depoda_barkod=depoda_barkod,
    )
    
    return snapshot