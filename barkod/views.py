# barkod/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal
import json
import io
from .utils import qr_kod_uret

from .models import BarkodSevkiyat, BarkodAdet, BarkodHareket, BarkodYazdirma
from stok.models import IhaleSevk, Depo, Raf


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def _cihaz_bilgisi(request):
    """Kullanıcının cihaz bilgisini çıkar (tablet takibi için)"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
    ip = request.META.get('REMOTE_ADDR', '')
    return user_agent, ip


def _barkod_uret(barkod_sevkiyat, adet):
    """
    Belirtilen sevkiyat için N adet benzersiz barkod oluştur.
    Format: KIK-PARTI-SIRA (örn: 4016-0979-0001)
    """
    ihale_sevk = barkod_sevkiyat.ihale_sevk
    ihale = ihale_sevk.ihale
    
    # KİK ve parti no'yu temizle
    kik = str(ihale.kik_no or '0000').strip()[:4].zfill(4)
    parti = str(ihale.parti_no or '0000').strip()[:4].zfill(4)
    
    # Bu prefix'te mevcut en yüksek sıra no'yu bul
    prefix = f"{kik}-{parti}-"
    son_adet = BarkodAdet.objects.filter(
        barkod__startswith=prefix
    ).order_by('-sira_no').first()
    
    baslangic_sira = (son_adet.sira_no + 1) if son_adet else 1
    
    # Toplu oluştur
    yeni_adetler = []
    for i in range(adet):
        sira = baslangic_sira + i
        barkod = f"{prefix}{sira:04d}"
        yeni_adetler.append(BarkodAdet(
            barkod_sevkiyat=barkod_sevkiyat,
            barkod=barkod,
            sira_no=sira,
            kalite_durumu='kabul',
            durum='depoda',
        ))
    
    BarkodAdet.objects.bulk_create(yeni_adetler)
    # ===== QR KODLARI ÜRET =====
    olusturulan_adetler = BarkodAdet.objects.filter(
        barkod_sevkiyat=barkod_sevkiyat,
        sira_no__gte=baslangic_sira,
        sira_no__lte=baslangic_sira + adet - 1
    )
    
    for adet_obj in olusturulan_adetler:
        try:
            qr_kod_uret(adet_obj, kaydet=True, box_size=12)
        except Exception as e:
            print(f"QR üretim hatası ({adet_obj.barkod}): {e}")
    # ===== QR BİTTİ =====
    
    # Sevkiyat özetini güncelle
    barkod_sevkiyat.toplam_adet = BarkodAdet.objects.filter(
        barkod_sevkiyat=barkod_sevkiyat
    ).count()
    barkod_sevkiyat.durum = 'tamamlandi'
    barkod_sevkiyat.seri_prefix = prefix
    barkod_sevkiyat.save()
    
    return baslangic_sira, baslangic_sira + adet - 1


# ============================================================
# 1. DASHBOARD
# ============================================================

@login_required
def barkod_dashboard(request):
    """Barkod modülü ana sayfası"""
    
    # İstatistikler
    toplam_sevkiyat = BarkodSevkiyat.objects.count()
    toplam_adet = BarkodAdet.objects.count()
    depoda = BarkodAdet.objects.filter(durum='depoda').count()
    uretimde = BarkodAdet.objects.filter(durum='uretimde').count()
    sevk_edildi = BarkodAdet.objects.filter(durum='sevk_edildi').count()
    red_edildi = BarkodAdet.objects.filter(kalite_durumu='red').count()
    
    # Son işlemler
    son_hareketler = BarkodHareket.objects.select_related(
        'barkod_adet', 'islem_yapan'
    ).order_by('-islem_tarihi')[:10]
    
    # Son sevkiyatlar
    son_sevkiyatlar = BarkodSevkiyat.objects.select_related(
        'ihale_sevk__ihale__tedarikci'
    ).order_by('-olusturma_tarihi')[:5]
    
    context = {
        'toplam_sevkiyat': toplam_sevkiyat,
        'toplam_adet': toplam_adet,
        'depoda': depoda,
        'uretimde': uretimde,
        'sevk_edildi': sevk_edildi,
        'red_edildi': red_edildi,
        'son_hareketler': son_hareketler,
        'son_sevkiyatlar': son_sevkiyatlar,
    }
    return render(request, 'barkod/dashboard.html', context)


# ============================================================
# 2. SEVK LİSTESİ (Teslim alınacaklar)
# ============================================================

@login_required
def sevk_listesi(request):
    """Teslim alınacak sevklerin listesi"""
    
    # Filtreler
    q = request.GET.get('q', '').strip()
    durum = request.GET.get('durum', '').strip()
    
    sevkiyatlar = BarkodSevkiyat.objects.select_related(
        'ihale_sevk__ihale__tedarikci'
    ).all().order_by('-olusturma_tarihi')
    
    if durum:
        sevkiyatlar = sevkiyatlar.filter(durum=durum)
    
    if q:
        sevkiyatlar = sevkiyatlar.filter(
            Q(ihale_sevk__ihale__kik_no__icontains=q) |
            Q(ihale_sevk__ihale__parti_no__icontains=q) |
            Q(ihale_sevk__ihale__tedarikci__unvan__icontains=q)
        )
    
    # Sayfalama
    paginator = Paginator(sevkiyatlar, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'durum': durum,
        'durum_secenekleri': BarkodSevkiyat.DURUM,
    }
    return render(request, 'barkod/sevk_listesi.html', context)


# ============================================================
# 3. TESLİM ALMA FORMU
# ============================================================

@login_required
def teslim_al(request, sevkiyat_id):
    """Teslim alma formu - adet ve miktar gir"""
    
    barkod_sevkiyat = get_object_or_404(
        BarkodSevkiyat.objects.select_related('ihale_sevk__ihale__tedarikci'),
        id=sevkiyat_id
    )
    
    # Mevcut adetleri al
    mevcut_adetler = BarkodAdet.objects.filter(
        barkod_sevkiyat=barkod_sevkiyat
    ).order_by('sira_no')
    
    context = {
        'barkod_sevkiyat': barkod_sevkiyat,
        'ihale_sevk': barkod_sevkiyat.ihale_sevk,
        'ihale': barkod_sevkiyat.ihale_sevk.ihale,
        'mevcut_adetler': mevcut_adetler,
        'mevcut_adet': mevcut_adetler.count(),
        'depolar': Depo.objects.filter(aktif_mi=True).order_by('ad'),
        'raflar': Raf.objects.all().order_by('kod'),
    }
    return render(request, 'barkod/teslim_al.html', context)


@login_required
def teslim_al_kaydet(request):
    """AJAX: N adet barkod oluştur"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'mesaj': 'Sadece POST'})
    
    try:
        data = json.loads(request.body)
        sevkiyat_id = data.get('sevkiyat_id')
        adet = int(data.get('adet', 0))
        toplam_miktar = Decimal(str(data.get('toplam_miktar', 0)))
        kalite_durumu = data.get('kalite_durumu', 'kabul')
        
        if adet <= 0:
            return JsonResponse({'success': False, 'mesaj': 'Adet 0 olamaz'})
        
        if adet > 1000:
            return JsonResponse({'success': False, 'mesaj': 'Tek seferde en fazla 1000 adet'})
        
        barkod_sevkiyat = get_object_or_404(BarkodSevkiyat, id=sevkiyat_id)
        
        # Ortalama birim hesapla
        ortalama = (toplam_miktar / adet) if adet > 0 else Decimal('0')
        
        with transaction.atomic():
            # N adet barkod oluştur
            baslangic, bitis = _barkod_uret(barkod_sevkiyat, adet)
            
            # Miktarları güncelle
            yeni_adetler = BarkodAdet.objects.filter(
                barkod_sevkiyat=barkod_sevkiyat,
                sira_no__gte=baslangic,
                sira_no__lte=bitis
            )
            yeni_adetler.update(
                olcum_miktar=ortalama,
                kalite_durumu=kalite_durumu,
            )
            
            # Sevkiyat özetini güncelle
            tum_adetler = BarkodAdet.objects.filter(barkod_sevkiyat=barkod_sevkiyat)
            barkod_sevkiyat.toplam_adet = tum_adetler.count()
            barkod_sevkiyat.toplam_miktar = toplam_miktar
            barkod_sevkiyat.ortalama_birim = ortalama
            barkod_sevkiyat.save()
            
            # Hareket kaydı
            for adet_obj in yeni_adetler:
                BarkodHareket.objects.create(
                    barkod_adet=adet_obj,
                    islem_tipi='teslim_alma',
                    yeni_durum='depoda',
                    islem_yapan=request.user,
                    notlar=f'Teslim alındı. Barkod serisi: {baslangic}-{bitis}',
                )
        
        return JsonResponse({
            'success': True,
            'mesaj': f'{adet} adet barkod oluşturuldu ({baslangic:04d}-{bitis:04d})',
            'baslangic': baslangic,
            'bitis': bitis,
            'sevkiyat_id': barkod_sevkiyat.id,
            'yazdir_url': f'/barkod/yazdir/{barkod_sevkiyat.id}/?baslangic={baslangic}&bitis={bitis}',
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'mesaj': f'Hata: {str(e)}'})


# ============================================================
# 4. BARKOD YAZDIRMA
# ============================================================

@login_required
def barkod_yazdir(request, sevkiyat_id):
    """Barkodları görüntüle ve yazdır"""
    
    barkod_sevkiyat = get_object_or_404(
        BarkodSevkiyat.objects.select_related('ihale_sevk__ihale__tedarikci'),
        id=sevkiyat_id
    )
    
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    
    adetler = BarkodAdet.objects.filter(barkod_sevkiyat=barkod_sevkiyat)
    
    if baslangic and bitis:
        adetler = adetler.filter(sira_no__gte=int(baslangic), sira_no__lte=int(bitis))
    
    adetler = adetler.order_by('sira_no')
    
    # Yazdırma kaydı oluştur
    if adetler.exists():
        ilk = adetler.first()
        son = adetler.last()
        BarkodYazdirma.objects.create(
            barkod_sevkiyat=barkod_sevkiyat,
            baslangic_sira=ilk.sira_no,
            bitis_sira=son.sira_no,
            adet=adetler.count(),
            yazdiran=request.user,
        )
    
    context = {
        'barkod_sevkiyat': barkod_sevkiyat,
        'ihale': barkod_sevkiyat.ihale_sevk.ihale,
        'adetler': adetler,
    }
    return render(request, 'barkod/barkod_yazdir.html', context)


@login_required
def barkod_yazdir_pdf(request, sevkiyat_id):
    """Barkodları PDF olarak indir (basit HTML yazdırma)"""
    # Şimdilik sadece HTML sayfasına yönlendir
    return redirect('barkod:barkod_yazdir', sevkiyat_id=sevkiyat_id)


# ============================================================
# 5. BARKOD OKUMA (Depo Yerleştirme)
# ============================================================

@login_required
def barkod_oku(request):
    """Barkod okuma ekranı - kamera/Bluetooth ile"""
    
    depolar = Depo.objects.filter(aktif_mi=True).order_by('ad')
    raflar = Raf.objects.all().order_by('kod')
    
    # Son okutulanlar (bu kullanıcı için)
    son_okutulanlar = BarkodHareket.objects.filter(
        islem_yapan=request.user,
        islem_tipi='depo_yerlestirme',
    ).select_related('barkod_adet', 'yeni_depo', 'yeni_raf').order_by('-islem_tarihi')[:20]
    
    context = {
        'depolar': depolar,
        'raflar': raflar,
        'son_okutulanlar': son_okutulanlar,
    }
    return render(request, 'barkod/barkod_oku.html', context)


@login_required
def barkod_oku_kaydet(request):
    """AJAX: Okutulan barkodu işle"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'mesaj': 'Sadece POST'})
    
    try:
        data = json.loads(request.body)
        barkod = data.get('barkod', '').strip()
        depo_id = data.get('depo_id')
        raf_id = data.get('raf_id')
        islem_tipi = data.get('islem_tipi', 'depo_yerlestirme')
        
        if not barkod:
            return JsonResponse({'success': False, 'mesaj': 'Barkod boş'})
        
        # Barkodu bul
        barkod_adet = BarkodAdet.objects.filter(barkod=barkod).first()
        
        if not barkod_adet:
            return JsonResponse({'success': False, 'mesaj': f'Barkod bulunamadı: {barkod}'})
        
        # Eski durum
        eski_durum = barkod_adet.durum
        eski_depo = barkod_adet.depo
        eski_raf = barkod_adet.raf
        
        # Yeni durum
        if islem_tipi == 'depo_yerlestirme':
            if depo_id:
                barkod_adet.depo = Depo.objects.filter(id=depo_id).first()
            if raf_id:
                barkod_adet.raf = Raf.objects.filter(id=raf_id).first()
            yeni_durum = 'depoda'
        elif islem_tipi == 'uretim_giris':
            yeni_durum = 'uretimde'
        elif islem_tipi == 'sevkiyat':
            yeni_durum = 'sevk_edildi'
        else:
            yeni_durum = 'depoda'
        
        barkod_adet.durum = yeni_durum
        barkod_adet.son_islem = islem_tipi
        barkod_adet.son_islem_tarihi = timezone.now()
        barkod_adet.save()
        
        # Hareket kaydı
        cihaz, ip = _cihaz_bilgisi(request)
        BarkodHareket.objects.create(
            barkod_adet=barkod_adet,
            islem_tipi=islem_tipi,
            eski_durum=eski_durum,
            yeni_durum=yeni_durum,
            eski_depo=eski_depo,
            yeni_depo=barkod_adet.depo,
            eski_raf=eski_raf,
            yeni_raf=barkod_adet.raf,
            islem_yapan=request.user,
            cihaz_bilgisi=cihaz,
            ip_adresi=ip,
        )
        
        return JsonResponse({
            'success': True,
            'mesaj': f'✅ {barkod} kaydedildi',
            'barkod': barkod,
            'urun': barkod_adet.barkod_sevkiyat.ihale_sevk.ihale.urun_adi or '-',
            'parti': barkod_adet.barkod_sevkiyat.ihale_sevk.ihale.parti_no,
            'boy': barkod_adet.barkod_sevkiyat.ihale_sevk.ihale.boy,
            'depo': barkod_adet.depo.ad if barkod_adet.depo else '-',
            'raf': barkod_adet.raf.kod if barkod_adet.raf else '-',
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'mesaj': f'Hata: {str(e)}'})


# ============================================================
# 6. BARKOD DETAY
# ============================================================

@login_required
def barkod_detay(request, barkod):
    """Tek barkod sorgula - detay sayfası"""
    
    barkod_adet = get_object_or_404(
        BarkodAdet.objects.select_related(
            'barkod_sevkiyat__ihale_sevk__ihale__tedarikci',
            'depo', 'raf'
        ),
        barkod=barkod
    )
    
    # Bu barkodun tüm hareketleri
    hareketler = BarkodHareket.objects.filter(
        barkod_adet=barkod_adet
    ).select_related('islem_yapan', 'yeni_depo', 'yeni_raf').order_by('-islem_tarihi')
    
    context = {
        'barkod_adet': barkod_adet,
        'hareketler': hareketler,
        'ihale': barkod_adet.barkod_sevkiyat.ihale_sevk.ihale,
    }
    return render(request, 'barkod/barkod_detay.html', context)


@login_required
def barkod_gecmis(request, barkod):
    """Barkodun tüm hareket geçmişi"""
    barkod_adet = get_object_or_404(BarkodAdet, barkod=barkod)
    hareketler = BarkodHareket.objects.filter(
        barkod_adet=barkod_adet
    ).select_related('islem_yapan').order_by('-islem_tarihi')
    
    return render(request, 'barkod/barkod_gecmis.html', {
        'barkod_adet': barkod_adet,
        'hareketler': hareketler,
    })


# ============================================================
# 7. RAPORLAR
# ============================================================

@login_required
def rapor_stok(request):
    """Stok durumu raporu - hangi depoda kaç adet"""
    
    depo_id = request.GET.get('depo', '')
    
    adetler = BarkodAdet.objects.filter(durum='depoda').select_related(
        'barkod_sevkiyat__ihale_sevk__ihale__tedarikci', 'depo', 'raf'
    )
    
    if depo_id:
        adetler = adetler.filter(depo_id=depo_id)
    
    # Depo bazlı özet
    depo_ozet = {}
    for adet in adetler:
        key = adet.depo.id if adet.depo else 0
        if key not in depo_ozet:
            depo_ozet[key] = {
                'depo': adet.depo,
                'adet': 0,
                'miktar': Decimal('0'),
            }
        depo_ozet[key]['adet'] += 1
        depo_ozet[key]['miktar'] += adet.olcum_miktar or Decimal('0')
    
    context = {
        'adetler': adetler.order_by('depo', 'raf', 'barkod')[:500],
        'depo_ozet': depo_ozet.values(),
        'toplam_adet': adetler.count(),
        'depolar': Depo.objects.filter(aktif_mi=True).order_by('ad'),
        'depo_id': depo_id,
    }
    return render(request, 'barkod/rapor_stok.html', context)