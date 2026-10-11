from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


class BarkodSevkiyat(models.Model):
    """
    Barkod sevkiyat başlığı — her IhaleSevk için 1 adet
    
    Bu model, mevcut IhaleSevk ile 1-1 ilişki kurar.
    Mevcut yapıya dokunmadan, barkod bilgilerini ayrı tutar.
    """
    
    DURUM = [
        ('beklemede', 'Beklemede'),
        ('kismi', 'Kısmi Kayıt'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    ]
    
    # ===== MEVCUT SEVK İLE BAĞLANTI =====
    ihale_sevk = models.OneToOneField(
        'stok.IhaleSevk',
        on_delete=models.PROTECT,
        related_name='barkod_sevkiyat',
        verbose_name="İhale Sevkiyat"
    )
    
    # ===== ÖZET BİLGİLER =====
    toplam_adet = models.IntegerField(
        default=0,
        verbose_name="Toplam Adet"
    )
    toplam_miktar = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal('0'),
        verbose_name="Toplam Miktar (m³)"
    )
    ortalama_birim = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0'),
        verbose_name="Ortalama Birim (m³/adet)"
    )
    
    # ===== DURUM =====
    durum = models.CharField(
        max_length=20,
        choices=DURUM,
        default='beklemede',
        verbose_name="Durum"
    )
    
    # ===== İŞLEM BİLGİLERİ =====
    olusturan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='olusturdugu_barkod_sevkiyatlar',
        verbose_name="Oluşturan"
    )
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturma Tarihi"
    )
    guncelleme_tarihi = models.DateTimeField(
        auto_now=True,
        verbose_name="Güncelleme Tarihi"
    )
    
    # ===== BARKOD SERİ =====
    seri_prefix = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Seri Prefix"
    )
    
    class Meta:
        verbose_name = "Barkod Sevkiyatı"
        verbose_name_plural = "Barkod Sevkiyatları"
        ordering = ['-olusturma_tarihi']
    
    def __str__(self):
        ihale = self.ihale_sevk.ihale
        return f"{ihale.kik_no or '?'}-{ihale.parti_no or '?'} ({self.toplam_adet} adet)"


class BarkodAdet(models.Model):
    """
    Her bir adet için ayrı kayıt — izlenebilirlik
    Üretim, sevkiyat, satış aşamalarında kullanılacak
    """
    
    DURUM = [
        ('depoda', 'Depoda'),
        ('uretimde', 'Üretimde'),
        ('sevk_edildi', 'Sevk Edildi'),
        ('satildi', 'Satıldı'),
        ('fire', 'Fire'),
        ('red', 'Red Edildi'),
        ('kayip', 'Kayıp'),
    ]
    
    KALITE = [
        ('kabul', 'Kabul Edildi'),
        ('kismi', 'Kısmi Kabul'),
        ('red', 'Red Edildi'),
    ]
    
    # ===== SEVK İLE BAĞLANTI =====
    barkod_sevkiyat = models.ForeignKey(
        BarkodSevkiyat,
        on_delete=models.CASCADE,
        related_name='adetler',
        verbose_name="Barkod Sevkiyatı"
    )
    
    # ===== BARKOD (BENZERSİZ) =====
    barkod = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Barkod"
    )
    sira_no = models.IntegerField(
        verbose_name="Sıra No"
    )
    
    # ===== ÖLÇÜM =====
    olcum_miktar = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Miktar (m³)"
    )
    
    # ===== KALİTE =====
    kalite_durumu = models.CharField(
        max_length=20,
        choices=KALITE,
        default='kabul',
        verbose_name="Kalite Durumu"
    )
    red_sebebi = models.TextField(
        blank=True,
        verbose_name="Red Sebebi"
    )
    
    # ===== KONUM =====
    durum = models.CharField(
        max_length=20,
        choices=DURUM,
        default='depoda',
        verbose_name="Durum"
    )
    depo = models.ForeignKey(
        'stok.Depo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Depo"
    )
    raf = models.ForeignKey(
        'stok.Raf',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Raf"
    )

    # ===== QR KOD =====
    qr_kod = models.ImageField(
        upload_to='barkod/qr/',
        null=True,
        blank=True,
        verbose_name="QR Kod"
    )
    qr_icerik = models.TextField(
        blank=True,
        verbose_name="QR İçeriği",
        help_text="QR kodda saklanan metin"
    )
    # ← ← ← BİTİŞ ← ← ←
    
    # ===== İZLENEBİLİRLİK =====
    son_islem = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Son İşlem"
    )
    son_islem_tarihi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Son İşlem Tarihi"
    )
    
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Oluşturma Tarihi"
    )
    
    class Meta:
        verbose_name = "Barkod Adedi"
        verbose_name_plural = "Barkod Adetleri"
        ordering = ['barkod_sevkiyat', 'sira_no']
        indexes = [
            models.Index(fields=['barkod']),
            models.Index(fields=['durum']),
            models.Index(fields=['kalite_durumu']),
        ]
    
    def __str__(self):
        return self.barkod


class BarkodHareket(models.Model):
    """
    Her barkod okutma işleminin log'u
    Kim, ne zaman, nerede, neden okuttu?
    """
    
    ISLEM_TIPI = [
        ('teslim_alma', 'Teslim Alma'),
        ('depo_yerlestirme', 'Depo Yerleştirme'),
        ('stok_sayim', 'Stok Sayım'),
        ('uretim_giris', 'Üretime Giriş'),
        ('uretim_cikis', 'Üretimden Çıkış'),
        ('sevkiyat', 'Sevkiyat'),
        ('iade', 'İade'),
        ('fire', 'Fire'),
        ('transfer', 'Transfer'),
    ]
    
    barkod_adet = models.ForeignKey(
        BarkodAdet,
        on_delete=models.CASCADE,
        related_name='hareketler',
        verbose_name="Barkod Adedi"
    )
    
    islem_tipi = models.CharField(
        max_length=30,
        choices=ISLEM_TIPI,
        verbose_name="İşlem Tipi"
    )
    
    # ===== KONUM BİLGİSİ =====
    eski_durum = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Eski Durum"
    )
    yeni_durum = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Yeni Durum"
    )
    eski_depo = models.ForeignKey(
        'stok.Depo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eski_depo_hareketleri',
        verbose_name="Eski Depo"
    )
    yeni_depo = models.ForeignKey(
        'stok.Depo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='yeni_depo_hareketleri',
        verbose_name="Yeni Depo"
    )
    eski_raf = models.ForeignKey(
        'stok.Raf',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eski_raf_hareketleri',
        verbose_name="Eski Raf"
    )
    yeni_raf = models.ForeignKey(
        'stok.Raf',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='yeni_raf_hareketleri',
        verbose_name="Yeni Raf"
    )
    
    # ===== İŞLEM BİLGİSİ =====
    islem_yapan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="İşlem Yapan"
    )
    islem_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name="İşlem Tarihi"
    )
    notlar = models.TextField(
        blank=True,
        verbose_name="Notlar"
    )
    
    # ===== CİHAZ BİLGİSİ (tablet takibi) =====
    cihaz_bilgisi = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Cihaz Bilgisi"
    )
    ip_adresi = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Adresi"
    )
    
    class Meta:
        verbose_name = "Barkod Hareketi"
        verbose_name_plural = "Barkod Hareketleri"
        ordering = ['-islem_tarihi']
        indexes = [
            models.Index(fields=['barkod_adet', 'islem_tarihi']),
            models.Index(fields=['islem_tipi']),
        ]
    
    def __str__(self):
        return f"{self.barkod_adet.barkod} - {self.get_islem_tipi_display()}"


class BarkodYazdirma(models.Model):
    """
    Barkod yazdırma kayıtları
    Kaç adet, ne zaman, kim yazdırdı?
    """
    
    barkod_sevkiyat = models.ForeignKey(
        BarkodSevkiyat,
        on_delete=models.CASCADE,
        related_name='yazdirmalar',
        verbose_name="Barkod Sevkiyatı"
    )
    
    baslangic_sira = models.IntegerField(verbose_name="Başlangıç Sıra")
    bitis_sira = models.IntegerField(verbose_name="Bitiş Sıra")
    adet = models.IntegerField(verbose_name="Yazdırılan Adet")
    
    yazdiran = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Yazdıran"
    )
    yazdirma_tarihi = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yazdırma Tarihi"
    )
    
    class Meta:
        verbose_name = "Barkod Yazdırma"
        verbose_name_plural = "Barkod Yazdırmaları"
        ordering = ['-yazdirma_tarihi']
    
    def __str__(self):
        return f"{self.barkod_sevkiyat} - {self.baslangic_sira}-{self.bitis_sira}"

class SilinenSevkiyatLog(models.Model):
    """Silinen sevkiyatların özet log'u - denetim ve kurtarma için"""
    
    # Silinen sevkiyat bilgileri
    sevkiyat_id = models.IntegerField(verbose_name="Sevkiyat ID")
    kik_no = models.CharField(max_length=20, blank=True, verbose_name="KİK No")
    parti_no = models.CharField(max_length=20, blank=True, verbose_name="Parti No")
    tedarikci = models.CharField(max_length=200, blank=True, verbose_name="Tedarikçi")
    urun_adi = models.CharField(max_length=200, blank=True, verbose_name="Ürün")
    boy = models.CharField(max_length=50, blank=True, verbose_name="Boy")
    
    # Sevkiyat değerleri
    sevk_miktar = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    sevk_adet = models.IntegerField(null=True, blank=True)
    barkod_sayisi = models.IntegerField(default=0, verbose_name="Silinen Barkod Sayısı")
    
    # Silme bilgileri
    silme_sebebi = models.TextField(verbose_name="Silme Sebebi")
    silen_kullanici = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Silen Kullanıcı"
    )
    silme_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Silme Tarihi")
    
    # Tam yedek (opsiyonel, sadece kritik veriler için)
    yedek_ozet = models.TextField(
        blank=True,
        verbose_name="Yedek Özet (JSON)",
        help_text="Barkod numaraları ve temel bilgiler"
    )
    
    class Meta:
        verbose_name = "Silinen Sevkiyat Log'u"
        verbose_name_plural = "Silinen Sevkiyat Log'ları"
        ordering = ['-silme_tarihi']
        indexes = [
            models.Index(fields=['kik_no', 'parti_no']),
            models.Index(fields=['-silme_tarihi']),
        ]
    
    def __str__(self):
        return f"{self.kik_no}-{self.parti_no} ({self.silme_tarihi:%d.m.Y %H:%M})"