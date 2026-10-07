# fabrika/urls.py
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import path, include, reverse
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from fabrika.roles import is_portal_user, ensure_default_groups
from stok.models import Urun, Ihale, StokHareket
from personel.models import Personel
from siparis.models import Siparis, Musteri
from finans.models import CariHesap, Banka

# Veritabanı hazır olduktan sonra istek akışında rol grupları oluşturulur.
# Aksi halde Render gibi ortamda startup sırasında auth_group tablosu bulunmayabilir.


def dashboard(request):
    """Gelişmiş Dashboard veya giriş seçimi ekranı."""
    if not request.user.is_authenticated:
        return render(request, 'site_entry.html')

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


class PortalLoginView(auth_views.LoginView):
    """Portal kullanıcılarını portal dashboard'a yönlendirir."""
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_to = self.request.POST.get('next') or self.request.GET.get('next')
        if redirect_to:
            return redirect_to

        user = self.request.user
        if user.is_staff:
            return '/admin/'
        if is_portal_user(user):
            return '/portal/'
        return '/'


def portal_user_required(view_func):
    """Sadece portal rolüne sahip kullanıcılar için erişim sağlar."""
    return user_passes_test(
        lambda u: u.is_authenticated and not u.is_staff and is_portal_user(u),
        login_url='/portal/login/'
    )(view_func)


@login_required(login_url='/portal/login/')
@portal_user_required
def portal_dashboard(request):
    """Portal kullanıcıları için rapor merkezi."""
    user_name = request.user.get_full_name() or request.user.username
    saat = timezone.now().hour
    if saat < 12:
        selamlama = 'Günaydın'
    elif saat < 18:
        selamlama = 'İyi günler'
    else:
        selamlama = 'İyi akşamlar'

    toplam_miktar = Ihale.objects.aggregate(toplam=Sum('toplam_ihale_miktari'))['toplam'] or 0
    toplam_kalan = Ihale.objects.aggregate(toplam=Sum('kalan_miktar'))['toplam'] or 0
    aktif_ihaleler = Ihale.objects.filter(durum='devam_ediyor').order_by('-id')
    toplam_ihale_miktar = aktif_ihaleler.aggregate(toplam=Sum('toplam_ihale_miktari'))['toplam'] or 0
    toplam_kalan_miktar = aktif_ihaleler.aggregate(toplam=Sum('kalan_miktar'))['toplam'] or 0
    aktif_ihale_sayisi = aktif_ihaleler.count()
    kritik_ihale_stok = Ihale.objects.filter(kalan_miktar__lt=10, kalan_miktar__gt=0, durum='devam_ediyor').count()
    son_hareketler = StokHareket.objects.filter(tarih__gte=timezone.now() - timedelta(days=7)).order_by('-tarih')[:10]
    kritik_stok = Urun.objects.filter(mevcut_miktar__lt=10, stokta_mi=True)[:10]

    toplam_alacak = CariHesap.objects.aggregate(toplam=Sum('alacak'))['toplam'] or 0
    toplam_borc = CariHesap.objects.aggregate(toplam=Sum('borc'))['toplam'] or 0
    net_bakiye = toplam_alacak - toplam_borc

    tip_dagilimi = Urun.objects.values('urun_tipi').annotate(adet=Count('id'), miktar=Sum('mevcut_miktar'))

    aylar_tr = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    son_6_ay = []
    siparis_verileri = []
    for i in range(5, -1, -1):
        ay = timezone.now() - timedelta(days=30*i)
        son_6_ay.append(aylar_tr[ay.month])
        ay_baslangic = ay.replace(day=1, hour=0, minute=0, second=0)
        if i == 0:
            ay_bitis = timezone.now()
        else:
            sonraki_ay = ay + timedelta(days=32)
            ay_bitis = sonraki_ay.replace(day=1, hour=0, minute=0, second=0) - timedelta(seconds=1)
        siparis_sayisi = Siparis.objects.filter(siparis_tarihi__range=(ay_baslangic, ay_bitis)).count()
        siparis_verileri.append(siparis_sayisi)

    report_groups = [
        {
            'title': 'Stok',
            'items': [
                ('/stok/rapor/dashboard/', 'Rapor Dashboard'),
                ('/stok/rapor/stok/', 'Stok Raporu'),
                ('/stok/rapor/fiili-stok/', 'Fiili Stok Takip'),
                ('/stok/rapor/stok-hareket/', 'Stok Hareketleri'),
                ('/stok/rapor/uretim/', 'Üretim Raporu'),
                ('/stok/rapor/finans/', 'Finans Raporu'),
                ('/stok/rapor/ihale-genel/', 'İhale Genel Raporu'),
                ('/stok/rapor/ihale-kik-icmal/', 'KİK İcmal Raporu'),
            ],
        },
        {
            'title': 'Personel',
            'items': [
                ('/personel/rapor/', 'Personel Raporu'),
            ],
        },
        {
            'title': 'Sipariş',
            'items': [
                ('/siparis/satis-raporu/', 'Satış Raporu'),
            ],
        },
        {
            'title': 'Yönetim',
            'items': [
                ('/admin/', 'Yönetim Paneli'),
            ],
        },
    ]
    return render(request, 'portal/dashboard.html', {
        'report_groups': report_groups,
        'total_reports': sum(len(group['items']) for group in report_groups),
        'user_name': user_name,
        'selamlama': selamlama,
        'toplam_miktar': toplam_miktar,
        'toplam_kalan': toplam_kalan,
        'aktif_ihale_sayisi': aktif_ihale_sayisi,
        'kritik_ihale_stok': kritik_ihale_stok,
        'aktif_ihaleler': aktif_ihaleler,
        'toplam_ihale_miktar': toplam_ihale_miktar,
        'toplam_kalan_miktar': toplam_kalan_miktar,
        'son_hareketler': son_hareketler,
        'kritik_stok': kritik_stok,
        'toplam_alacak': toplam_alacak,
        'toplam_borc': toplam_borc,
        'net_bakiye': net_bakiye,
        'tip_dagilimi': tip_dagilimi,
        'son_6_ay': son_6_ay,
        'siparis_verileri': siparis_verileri,
    })


admin_logout_view = auth_views.LogoutView.as_view(next_page='/')
portal_logout_view = auth_views.LogoutView.as_view(next_page='/')

def hakkimizda_view(request):
    return render(request, 'site_hakkimizda.html')


def urunlerimiz_view(request):
    return render(request, 'site_urunlerimiz.html')


def hizmetlerimiz_view(request):
    return render(request, 'site_hizmetlerimiz.html')


def referanslarimiz_view(request):
    return render(request, 'site_referanslarimiz.html')


def bize_ulasin_view(request):
    return render(request, 'site_bize_ulasin.html')


urlpatterns = [
    # ===== ESKİ URL YÖNLENDİRMESİ =====
    path('admin/stok/ihaleparti/', redirect_ihaleparti),
    path('admin/stok/ihaleparti/<path:path>/', redirect_ihaleparti),

    # ===== PORTAL GİRİŞ/ÇIKIŞ =====
    path('portal/login/', PortalLoginView.as_view(template_name='portal/login.html'), name='portal_login'),
    path('portal/logout/', portal_logout_view, name='portal_logout'),
    path('portal/', portal_dashboard, name='portal_dashboard'),

    # ===== ANA URL'LER =====
    path('admin/logout/', admin_logout_view, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('hakkimizda/', hakkimizda_view, name='hakkimizda'),
    path('urunlerimiz/', urunlerimiz_view, name='urunlerimiz'),
    path('hizmetlerimiz/', hizmetlerimiz_view, name='hizmetlerimiz'),
    path('referanslarimiz/', referanslarimiz_view, name='referanslarimiz'),
    path('bize-ulasin/', bize_ulasin_view, name='bize_ulasin'),
    path('stok/', include('stok.urls')),
    path('personel/', include('personel.urls')),
    path('siparis/', include('siparis.urls')),
    path('finans/', include('finans.urls')),
]