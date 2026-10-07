from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from stok.models import Urun

# ==================== SATIŞ (MEVCUT SİPARİŞ MODELİ GELİŞTİRİLDİ) ====================

class Satis(models.Model):
    """Satış işlemleri"""
    SATIS_DURUMU = (
        ('teklif', 'Teklif'),
        ('onaylandi', 'Onaylandı'),
        ('hazirlaniyor', 'Hazırlanıyor'),
        ('sevk_edildi', 'Sevk Edildi'),
        ('teslim_edildi', 'Teslim Edildi'),
        ('iptal', 'İptal'),
    )
    
    ODEME_DURUMU = (
        ('beklemede', 'Beklemede'),
        ('kismi', 'Kısmi Ödeme'),
        ('tamam', 'Tamamlandı'),
        ('gecikti', 'Gecikti'),
    )
    
    # Temel Bilgiler
    satis_no = models.CharField(max_length=50, unique=True, blank=True, editable=False, verbose_name="Satış No")
    musteri = models.ForeignKey('Musteri', on_delete=models.CASCADE, verbose_name="Müşteri")
    siparis_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Sipariş Tarihi")
    teslim_tarihi = models.DateField(null=True, blank=True, verbose_name="Teslim Tarihi")
    
    # Ürün Bilgileri
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.FloatField(verbose_name="Miktar (m³)")
    birim_fiyat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Birim Fiyat (TL)")
    toplam_tutar = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Toplam Tutar")
    
    # Durum Bilgileri
    durum = models.CharField(max_length=20, choices=SATIS_DURUMU, default='teklif', verbose_name="Durum")
    odeme_durumu = models.CharField(max_length=20, choices=ODEME_DURUMU, default='beklemede', verbose_name="Ödeme Durumu")
    
    # İrsaliye ve Fatura
    irsaliye_no = models.CharField(max_length=50, blank=True, verbose_name="İrsaliye No")
    fatura_no = models.CharField(max_length=50, blank=True, verbose_name="Fatura No")
    
    # Açıklama
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    # Sistem Bilgileri
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Satış"
        verbose_name_plural = "Satışlar"
        ordering = ['-siparis_tarihi']
    
    def save(self, *args, **kwargs):
        # Otomatik satış numarası oluştur
        if not self.satis_no:
            son_kayit = Satis.objects.all().order_by('id').last()
            if son_kayit and son_kayit.satis_no:
                try:
                    son_sayi = int(son_kayit.satis_no.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.satis_no = f"SAT-{yeni_sayi:04d}"
        
        # Toplam tutarı hesapla
        if self.miktar and self.birim_fiyat:
            self.toplam_tutar = Decimal(str(self.miktar)) * self.birim_fiyat
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.satis_no} - {self.musteri.unvan}"


class SatisDetay(models.Model):
    """Satış detayları (ürün bazlı)"""
    satis = models.ForeignKey(Satis, on_delete=models.CASCADE, related_name='detaylar', verbose_name="Satış")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.FloatField(verbose_name="Miktar (m³)")
    birim_fiyat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Birim Fiyat (TL)")
    toplam_tutar = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Toplam Tutar")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Satış Detayı"
        verbose_name_plural = "Satış Detayları"
    
    def save(self, *args, **kwargs):
        if self.miktar and self.birim_fiyat:
            self.toplam_tutar = Decimal(str(self.miktar)) * self.birim_fiyat
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.satis.satis_no} - {self.urun.urun_adi}"


class SatisIade(models.Model):
    """Satış iadeleri"""
    satis = models.ForeignKey(Satis, on_delete=models.CASCADE, related_name='iadeler', verbose_name="Satış")
    iade_no = models.CharField(max_length=50, unique=True, blank=True, editable=False, verbose_name="İade No")
    iade_tarihi = models.DateField(auto_now_add=True, verbose_name="İade Tarihi")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.FloatField(verbose_name="İade Miktarı (m³)")
    sebep = models.TextField(verbose_name="İade Sebebi")
    onaylandi_mi = models.BooleanField(default=False, verbose_name="Onaylandı mı?")
    onaylayan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Onaylayan")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Satış İadesi"
        verbose_name_plural = "Satış İadeleri"
        ordering = ['-iade_tarihi']
    
    def save(self, *args, **kwargs):
        if not self.iade_no:
            son_kayit = SatisIade.objects.all().order_by('id').last()
            if son_kayit and son_kayit.iade_no:
                try:
                    son_sayi = int(son_kayit.iade_no.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.iade_no = f"IADE-{yeni_sayi:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.iade_no} - {self.satis.satis_no}"

class Musteri(models.Model):
    musteri_kodu = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Müşteri Kodu"
    )
    unvan = models.CharField(max_length=200, verbose_name="Ünvan")
    vergi_dairesi = models.CharField(max_length=100, verbose_name="Vergi Dairesi")
    vergi_no = models.CharField(max_length=10, verbose_name="Vergi No")
    adres = models.TextField(verbose_name="Adres")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-Posta")
    yetkili = models.CharField(max_length=100, blank=True, verbose_name="Yetkili Kişi")
    
    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
    
    def __str__(self):
        return f"{self.musteri_kodu} - {self.unvan}"

    def save(self, *args, **kwargs):
        if not self.musteri_kodu:
            son_kayit = Musteri.objects.all().order_by('id').last()
            if son_kayit and son_kayit.musteri_kodu:
                try:
                    son_sayi = int(son_kayit.musteri_kodu.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.musteri_kodu = f"MUS-{yeni_sayi:04d}"
        super().save(*args, **kwargs)

class Siparis(models.Model):
    SIPARIS_DURUMU = (
        ('beklemede', 'Beklemede'),
        ('isleniyor', 'İşleniyor'),
        ('hazir', 'Hazır'),
        ('teslim_edildi', 'Teslim Edildi'),
        ('iptal', 'İptal'),
    )
    
    siparis_no = models.CharField(max_length=50, unique=True, verbose_name="Sipariş No")
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, verbose_name="Müşteri")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.FloatField(verbose_name="Miktar (m³)")
    birim_fiyat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Birim Fiyat")
    toplam_tutar = models.DecimalField(max_digits=12, decimal_places=2, editable=False, verbose_name="Toplam Tutar")
    durum = models.CharField(max_length=20, choices=SIPARIS_DURUMU, default='beklemede', verbose_name="Durum")
    siparis_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Sipariş Tarihi")
    teslim_tarihi = models.DateField(null=True, blank=True, verbose_name="Teslim Tarihi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering = ['-siparis_tarihi']
    
    def save(self, *args, **kwargs):
        self.toplam_tutar = Decimal(self.miktar) * self.birim_fiyat
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.siparis_no} - {self.musteri.unvan}"