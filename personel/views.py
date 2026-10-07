# personel/views.py
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.http import JsonResponse
from .models import Personel, Departman, Izin, Vardiya
from datetime import datetime, timedelta
from django.utils import timezone


def personel_raporu(request):
    """Personel raporu"""
    # Genel istatistikler
    toplam_personel = Personel.objects.count()
    aktif_personel = Personel.objects.filter(calisma_durumu='aktif').count()
    izinli_personel = Personel.objects.filter(calisma_durumu='izinli').count()
    
    # Departman bazlı personel sayısı
    departman_dagilimi = Departman.objects.annotate(
        personel_sayisi=Count('personel')
    ).filter(personel_sayisi__gt=0)
    
    # Cinsiyet dağılımı
    erkek_sayisi = Personel.objects.filter(cinsiyet='erkek').count()
    kadin_sayisi = Personel.objects.filter(cinsiyet='kadin').count()
    
    # Eğitim durumu dağılımı
    egitim_dagilimi = Personel.objects.values('egitim_durumu').annotate(
        sayi=Count('id')
    )
    
    # Bu ayki izinler
    bugun = timezone.now().date()
    ay_baslangic = bugun.replace(day=1)
    bu_ay_izinler = Izin.objects.filter(
        baslangic_tarihi__gte=ay_baslangic,
        durum='onaylandi'
    )
    
    context = {
        'toplam_personel': toplam_personel,
        'aktif_personel': aktif_personel,
        'izinli_personel': izinli_personel,
        'departman_dagilimi': departman_dagilimi,
        'erkek_sayisi': erkek_sayisi,
        'kadin_sayisi': kadin_sayisi,
        'egitim_dagilimi': egitim_dagilimi,
        'bu_ay_izinler': bu_ay_izinler,
    }
    return render(request, 'personel/personel_raporu.html', context)