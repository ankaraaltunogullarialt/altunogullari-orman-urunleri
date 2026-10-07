# personel/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Departman(models.Model):
    """Departmanlar"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Departman Adı")
    kod = models.CharField(max_length=20, unique=True, verbose_name="Departman Kodu")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Departman"
        verbose_name_plural = "Departmanlar"
        ordering = ['ad']
    
    def __str__(self):
        return f"{self.kod} - {self.ad}"


class Personel(models.Model):
    """Personel bilgileri"""
    
    # Medeni Durum
    MEDENI_DURUM = (
        ('bekar', 'Bekar'),
        ('evli', 'Evli'),
        ('bosanmis', 'Boşanmış'),
        ('dul', 'Dul'),
    )
    
    # Eğitim Durumu
    EGITIM_DURUMU = (
        ('ilkokul', 'İlkokul'),
        ('ortaokul', 'Ortaokul'),
        ('lise', 'Lise'),
        ('onlisans', 'Ön Lisans'),
        ('lisans', 'Lisans'),
        ('yuksek_lisans', 'Yüksek Lisans'),
        ('doktora', 'Doktora'),
    )
    
    # Kan Grubu
    KAN_GRUBU = (
        ('A Rh+', 'A Rh+'),
        ('A Rh-', 'A Rh-'),
        ('B Rh+', 'B Rh+'),
        ('B Rh-', 'B Rh-'),
        ('AB Rh+', 'AB Rh+'),
        ('AB Rh-', 'AB Rh-'),
        ('0 Rh+', '0 Rh+'),
        ('0 Rh-', '0 Rh-'),
    )
    
    # Cinsiyet
    CINSIYET = (
        ('erkek', 'Erkek'),
        ('kadin', 'Kadın'),
    )
    
    # Çalışma Durumu
    CALISMA_DURUMU = (
        ('aktif', 'Aktif'),
        ('izinli', 'İzinli'),
        ('raporlu', 'Raporlu'),
        ('cikis', 'Çıkış Yaptı'),
    )
    
    # Kullanıcı ile ilişki (Django User)
    user = models.OneToOneField(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Kullanıcı Hesabı",
        help_text="Sisteme giriş yapacak kullanıcı hesabı"
    )
    
    # Temel Bilgiler
    sicil_no = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Sicil No"
    )
    ad = models.CharField(max_length=50, verbose_name="Ad")
    soyad = models.CharField(max_length=50, verbose_name="Soyad")
    tc_kimlik = models.CharField(max_length=11, unique=True, verbose_name="TC Kimlik No")
    dogum_tarihi = models.DateField(verbose_name="Doğum Tarihi")
    dogum_yeri = models.CharField(max_length=100, blank=True, verbose_name="Doğum Yeri")
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET, verbose_name="Cinsiyet")
    kan_grubu = models.CharField(max_length=10, choices=KAN_GRUBU, blank=True, verbose_name="Kan Grubu")
    medeni_durum = models.CharField(max_length=20, choices=MEDENI_DURUM, blank=True, verbose_name="Medeni Durum")
    cocuk_sayisi = models.IntegerField(default=0, verbose_name="Çocuk Sayısı")
    
    # İletişim Bilgileri
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    cep_telefonu = models.CharField(max_length=15, blank=True, verbose_name="Cep Telefonu")
    email = models.EmailField(blank=True, verbose_name="E-Posta")
    adres = models.TextField(verbose_name="Adres")
    acil_durum_kisi = models.CharField(max_length=100, blank=True, verbose_name="Acil Durum Kişisi")
    acil_durum_telefon = models.CharField(max_length=15, blank=True, verbose_name="Acil Durum Telefonu")
    
    # İş Bilgileri
    departman = models.ForeignKey(
        Departman, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Departman"
    )
    unvan = models.CharField(max_length=100, blank=True, verbose_name="Ünvan")
    ise_giris_tarihi = models.DateField(verbose_name="İşe Giriş Tarihi")
    isten_cikis_tarihi = models.DateField(null=True, blank=True, verbose_name="İşten Çıkış Tarihi")
    calisma_durumu = models.CharField(max_length=20, choices=CALISMA_DURUMU, default='aktif', verbose_name="Çalışma Durumu")
    
    # Maaş Bilgileri
    maas = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Maaş (TL)")
    maas_birimi = models.CharField(max_length=20, default='aylik', verbose_name="Maaş Birimi")
    ek_odeme = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ek Ödeme (TL)")
    prim_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Prim Oranı (%)")
    
    # Eğitim Bilgileri
    egitim_durumu = models.CharField(max_length=20, choices=EGITIM_DURUMU, blank=True, verbose_name="Eğitim Durumu")
    okul = models.CharField(max_length=200, blank=True, verbose_name="Mezun Olunan Okul")
    bolum = models.CharField(max_length=200, blank=True, verbose_name="Bölüm")
    mezuniyet_yili = models.IntegerField(null=True, blank=True, verbose_name="Mezuniyet Yılı")
    
    # Diğer Bilgiler
    ehliyet = models.CharField(max_length=50, blank=True, verbose_name="Ehliyet")
    yabanci_dil = models.CharField(max_length=100, blank=True, verbose_name="Yabancı Dil")
    bildigi_diller = models.TextField(blank=True, verbose_name="Bildiği Diller")
    sertifikalar = models.TextField(blank=True, verbose_name="Sertifikalar")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    
    # Sistem Bilgileri
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='olusturulan_personel',
        verbose_name="Oluşturan"
    )
    
    class Meta:
        verbose_name = "Personel"
        verbose_name_plural = "Personeller"
        ordering = ['ad', 'soyad']
    
    def __str__(self):
        return f"{self.ad} {self.soyad} ({self.sicil_no})"
    
    def tam_adi(self):
        return f"{self.ad} {self.soyad}"
    
    def yas(self):
        """Personelin yaşını hesapla"""
        today = timezone.now().date()
        return today.year - self.dogum_tarihi.year - (
            (today.month, today.day) < (self.dogum_tarihi.month, self.dogum_tarihi.day)
        )
    
    def calisma_suresi(self):
        """Çalışma süresini hesapla (yıl, ay)"""
        if not self.ise_giris_tarihi:
            return "-"
        today = timezone.now().date()
        yil = today.year - self.ise_giris_tarihi.year
        ay = today.month - self.ise_giris_tarihi.month
        if ay < 0:
            yil -= 1
            ay += 12
        if yil == 0:
            return f"{ay} ay"
        return f"{yil} yıl {ay} ay"
    
    def toplam_maas(self):
        """Toplam maaş (maaş + ek ödeme)"""
        return self.maas + self.ek_odeme

    def save(self, *args, **kwargs):
        if not self.sicil_no:
            son_kayit = Personel.objects.all().order_by('id').last()
            if son_kayit and son_kayit.sicil_no:
                try:
                    son_sayi = int(son_kayit.sicil_no.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.sicil_no = f"PER-{yeni_sayi:04d}"
        super().save(*args, **kwargs)


class Vardiya(models.Model):
    """Vardiya takvimi"""
    VARDIA_TIPI = (
        ('sabah', 'Sabah Vardiyası (08:00-16:00)'),
        ('aksam', 'Akşam Vardiyası (16:00-00:00)'),
        ('gece', 'Gece Vardiyası (00:00-08:00)'),
        ('normal', 'Normal Mesai (09:00-18:00)'),
    )
    
    personel = models.ForeignKey(Personel, on_delete=models.CASCADE, related_name='vardiyalar', verbose_name="Personel")
    vardiya_tipi = models.CharField(max_length=20, choices=VARDIA_TIPI, verbose_name="Vardiya Tipi")
    tarih = models.DateField(verbose_name="Tarih")
    baslangic_saati = models.TimeField(verbose_name="Başlangıç Saati")
    bitis_saati = models.TimeField(verbose_name="Bitiş Saati")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vardiya"
        verbose_name_plural = "Vardiyalar"
        ordering = ['-tarih', 'personel']
        unique_together = ['personel', 'tarih']
    
    def __str__(self):
        return f"{self.personel.tam_adi()} - {self.get_vardiya_tipi_display()} ({self.tarih})"


class Izin(models.Model):
    """İzin takibi"""
    IZIN_TIPI = (
        ('yillik', 'Yıllık İzin'),
        ('hastalik', 'Hastalık İzni'),
        ('mazeret', 'Mazeret İzni'),
        ('dogum', 'Doğum İzni'),
        ('olum', 'Ölüm İzni'),
        ('evlilik', 'Evlilik İzni'),
        ('ucretsiz', 'Ücretsiz İzin'),
        ('diger', 'Diğer'),
    )
    
    IZIN_DURUMU = (
        ('beklemede', 'Beklemede'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
        ('iptal', 'İptal'),
    )
    
    personel = models.ForeignKey(Personel, on_delete=models.CASCADE, related_name='izinler', verbose_name="Personel")
    izin_tipi = models.CharField(max_length=20, choices=IZIN_TIPI, verbose_name="İzin Tipi")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    gun_sayisi = models.IntegerField(verbose_name="Gün Sayısı")
    aciklama = models.TextField(verbose_name="Açıklama")
    durum = models.CharField(max_length=20, choices=IZIN_DURUMU, default='beklemede', verbose_name="Durum")
    onaylayan = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='onaylanan_izinler',
        verbose_name="Onaylayan"
    )
    onay_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Onay Tarihi")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "İzin"
        verbose_name_plural = "İzinler"
        ordering = ['-baslangic_tarihi']
    
    def __str__(self):
        return f"{self.personel.tam_adi()} - {self.get_izin_tipi_display()} ({self.baslangic_tarihi})"
    
    def izin_suresi(self):
        """İzin süresini hesapla"""
        delta = self.bitis_tarihi - self.baslangic_tarihi
        return delta.days + 1


class MesaiTakip(models.Model):
    """Günlük mesai takibi"""
    personel = models.ForeignKey(Personel, on_delete=models.CASCADE, related_name='mesailer', verbose_name="Personel")
    tarih = models.DateField(verbose_name="Tarih")
    gelis_saati = models.TimeField(verbose_name="Geliş Saati")
    cikis_saati = models.TimeField(null=True, blank=True, verbose_name="Çıkış Saati")
    toplam_calisma = models.DurationField(null=True, blank=True, verbose_name="Toplam Çalışma")
    fazla_mesai = models.DurationField(null=True, blank=True, verbose_name="Fazla Mesai")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Mesai Takibi"
        verbose_name_plural = "Mesai Takipleri"
        ordering = ['-tarih', 'personel']
        unique_together = ['personel', 'tarih']
    
    def __str__(self):
        return f"{self.personel.tam_adi()} - {self.tarih}"