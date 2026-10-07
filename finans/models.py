from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from siparis.models import Musteri
from stok.models import Tedarikci

class CariHesap(models.Model):
    """Müşteri ve tedarikçi cari hesapları"""
    HESAP_TIPI = (
        ('musteri', 'Müşteri'),
        ('tedarikci', 'Tedarikçi'),
    )
    
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Müşteri")
    tedarikci = models.ForeignKey(Tedarikci, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Tedarikçi")
    hesap_tipi = models.CharField(max_length=20, choices=HESAP_TIPI, verbose_name="Hesap Tipi")
    bakiye = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Bakiye")
    borc = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Toplam Borç")
    alacak = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Toplam Alacak")
    limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Kredi Limiti")
    risk_orani = models.FloatField(default=0, verbose_name="Risk Oranı (%)")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Cari Hesap"
        verbose_name_plural = "Cari Hesaplar"
    
    def __str__(self):
        if self.musteri:
            return f"Müşteri: {self.musteri.unvan} - Bakiye: {self.bakiye} TL"
        return f"Tedarikçi: {self.tedarikci.unvan} - Bakiye: {self.bakiye} TL"
    
    def bakiye_hesapla(self):
        """Güncel bakiyeyi hesapla"""
        hareketler = self.cari_hareket.all()
        borc_toplam = hareketler.filter(hareket_tipi='borc').aggregate(models.Sum('tutar'))['tutar__sum'] or 0
        alacak_toplam = hareketler.filter(hareket_tipi='alacak').aggregate(models.Sum('tutar'))['tutar__sum'] or 0
        self.borc = borc_toplam
        self.alacak = alacak_toplam
        self.bakiye = alacak_toplam - borc_toplam
        self.save()
        return self.bakiye

class CariHareket(models.Model):
    """Cari hesap hareketleri"""
    HAREKET_TIPI = (
        ('borc', 'Borç (Müşteri Borcu)'),
        ('alacak', 'Alacak (Müşteri Ödemesi)'),
    )
    KAYNAK_TIPI = (
        ('fatura', 'Fatura'),
        ('tahsilat', 'Tahsilat'),
        ('odeme', 'Ödeme'),
        ('diger', 'Diğer'),
    )
    
    cari = models.ForeignKey(CariHesap, on_delete=models.CASCADE, related_name='cari_hareket', verbose_name="Cari Hesap")
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    kaynak_tipi = models.CharField(max_length=20, choices=KAYNAK_TIPI, verbose_name="Kaynak Tipi")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (TL)")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    vade_tarihi = models.DateField(null=True, blank=True, verbose_name="Vade Tarihi")
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan")
    belge_no = models.CharField(max_length=50, blank=True, verbose_name="Belge No")
    
    class Meta:
        verbose_name = "Cari Hareket"
        verbose_name_plural = "Cari Hareketler"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.cari} - {self.get_hareket_tipi_display()} - {self.tutar} TL"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Kayıt sonrası cari bakiyeyi güncelle
        self.cari.bakiye_hesapla()

class Banka(models.Model):
    """Banka hesap yönetimi"""
    BANKA_TIPI = (
        ('vadesiz', 'Vadesiz Mevduat'),
        ('vadeli', 'Vadeli Mevduat'),
        ('kredi', 'Kredi Hesabı'),
    )
    
    ad = models.CharField(max_length=200, verbose_name="Banka Adı")
    sube = models.CharField(max_length=200, verbose_name="Şube")
    hesap_no = models.CharField(max_length=50, unique=True, verbose_name="Hesap No")
    iban = models.CharField(max_length=34, unique=True, verbose_name="IBAN")
    hesap_tipi = models.CharField(max_length=20, choices=BANKA_TIPI, default='vadesiz', verbose_name="Hesap Tipi")
    bakiye = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Bakiye")
    para_birimi = models.CharField(max_length=3, default='TRY', verbose_name="Para Birimi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Banka Hesabı"
        verbose_name_plural = "Banka Hesapları"
    
    def __str__(self):
        return f"{self.ad} - {self.hesap_no} ({self.bakiye} {self.para_birimi})"

class BankaHareket(models.Model):
    """Banka hareketleri"""
    HAREKET_TIPI = (
        ('giris', 'Giriş'),
        ('cikis', 'Çıkış'),
    )
    
    banka = models.ForeignKey(Banka, on_delete=models.CASCADE, related_name='banka_hareket', verbose_name="Banka")
    hareket_tipi = models.CharField(max_length=10, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan")
    
    class Meta:
        verbose_name = "Banka Hareketi"
        verbose_name_plural = "Banka Hareketleri"
        ordering = ['-tarih']
    
    def __str__(self):
        return f"{self.banka} - {self.get_hareket_tipi_display()} - {self.tutar} TL"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Banka bakiyesini güncelle
        if self.hareket_tipi == 'giris':
            self.banka.bakiye += self.tutar
        else:
            self.banka.bakiye -= self.tutar
        self.banka.save()