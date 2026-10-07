# siparis/views.py
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Satis, SatisIade
from django.utils import timezone
from datetime import timedelta


def satis_raporu(request):
    """Satış raporu"""
    # Genel istatistikler
    toplam_satis = Satis.objects.count()
    toplam_tutar = Satis.objects.aggregate(toplam=Sum('toplam_tutar'))['toplam'] or 0
    
    # Durum bazlı
    durum_dagilimi = Satis.objects.values('durum').annotate(
        adet=Count('id'),
        tutar=Sum('toplam_tutar')
    )
    
    # Son 30 gün
    son_30_gun = timezone.now() - timedelta(days=30)
    son_satislar = Satis.objects.filter(siparis_tarihi__gte=son_30_gun)[:20]
    
    # İadeler
    toplam_iade = SatisIade.objects.filter(onaylandi_mi=True).count()
    
    context = {
        'toplam_satis': toplam_satis,
        'toplam_tutar': toplam_tutar,
        'durum_dagilimi': durum_dagilimi,
        'son_satislar': son_satislar,
        'toplam_iade': toplam_iade,
    }
    return render(request, 'siparis/satis_raporu.html', context)