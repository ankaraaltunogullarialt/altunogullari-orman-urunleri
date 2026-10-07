# stok/models.py
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


# ==================== NACE KODU ====================
class NACEKodu(models.Model):
    """NACE kodları - kullanıcı ekleyebilir, sistem sabitleri var"""
    kod = models.CharField(max_length=20, unique=True, verbose_name="NACE Kodu")
    aciklama = models.TextField(verbose_name="Açıklama")
    sistem_kodu = models.BooleanField(default=False, verbose_name="Sistem Kodu (Sabit)")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "NACE Kodu"
        verbose_name_plural = "NACE Kodları"
        ordering = ['kod']
    
    def __str__(self):
        return f"{self.kod} - {self.aciklama[:60]}"


# ==================== TEDARİKÇİ TİPİ ====================
class TedarikciTipi(models.Model):
    """Kullanıcı tarafından eklenebilen tedarikçi tipleri"""
    ad = models.CharField(max_length=100, unique=True, verbose_name="Tip Adı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    sistem_tipi = models.BooleanField(default=False, verbose_name="Sistem Tipi (Sabit)")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tedarikçi Tipi"
        verbose_name_plural = "Tedarikçi Tipleri"
        ordering = ['-sistem_tipi', 'ad']
    
    def __str__(self):
        return f"{self.ad} {'(Sistem)' if self.sistem_tipi else ''}"


# ==================== TEDARİKÇİ ====================
class Tedarikci(models.Model):
    TEDARIKCI_TIPI = (
        ('oim', 'Orman İşletme Müdürlüğü'),
        ('sahis', 'Şahıs/Özel'),
        ('ihale', 'İhale'),
        ('kooperatif', 'Kooperatif'),
        ('firma', 'Özel Firma'),
    )
    
    kod = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Tedarikçi Kodu"
    )
    unvan = models.CharField(max_length=200, verbose_name="Ünvan/Ad")
    
    tedarikci_tipi = models.ForeignKey(
        TedarikciTipi, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Tedarikçi Tipi (Yeni)"
    )
    
    tedarikci_tipi_eski = models.CharField(
        max_length=20, 
        choices=TEDARIKCI_TIPI, 
        default='sahis', 
        verbose_name="Tedarikçi Tipi"
    )
    
    vergi_dairesi = models.CharField(max_length=100, blank=True, verbose_name="Vergi Dairesi")
    vergi_no = models.CharField(max_length=10, blank=True, verbose_name="Vergi No")
    adres = models.TextField(blank=True, verbose_name="Adres")
    telefon = models.CharField(max_length=15, blank=True, verbose_name="Telefon")
    yetkili = models.CharField(max_length=100, blank=True, verbose_name="Yetkili Kişi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tedarikçi"
        verbose_name_plural = "Tedarikçiler"
        ordering = ['unvan']
    
    def __str__(self):
        if self.tedarikci_tipi:
            return f"{self.kod} - {self.unvan} ({self.tedarikci_tipi.ad})"
        return f"{self.kod} - {self.unvan} ({self.get_tedarikci_tipi_eski_display()})"
    
    def get_tip_display(self):
        if self.tedarikci_tipi:
            return self.tedarikci_tipi.ad
        return self.get_tedarikci_tipi_eski_display()
    
    def get_tip_icon(self):
        tip_adi = self.get_tip_display()
        if 'OİM' in tip_adi or 'orman' in tip_adi.lower():
            return '🌲'
        elif 'şahıs' in tip_adi.lower():
            return '👤'
        elif 'ihale' in tip_adi.lower():
            return '🏛️'
        elif 'kooperatif' in tip_adi.lower():
            return '🤝'
        elif 'firma' in tip_adi.lower():
            return '🏢'
        return '📌'
    
    def save(self, *args, **kwargs):
        if not self.tedarikci_tipi and self.tedarikci_tipi_eski:
            tip_ad = dict(self.TEDARIKCI_TIPI).get(self.tedarikci_tipi_eski)
            if tip_ad:
                tip, created = TedarikciTipi.objects.get_or_create(
                    ad=tip_ad,
                    defaults={
                        'sistem_tipi': True,
                        'aktif_mi': True,
                        'aciklama': f'Sistem tarafından oluşturuldu - {self.tedarikci_tipi_eski}'
                    }
                )
                self.tedarikci_tipi = tip
        
        if not self.kod:
            son_kayit = Tedarikci.objects.all().order_by('id').last()
            if son_kayit and son_kayit.kod:
                try:
                    son_sayi = int(son_kayit.kod.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.kod = f"TED-{yeni_sayi:04d}"
        super().save(*args, **kwargs)


# ==================== ÜRÜN ====================
class Urun(models.Model):
    URUN_TIPI = (
        ('hammadde', 'Hammadde'),
        ('mamul', 'Mamul'),
        ('yan_urun', 'Yan Ürün'),
        ('atık', 'Atık'),
    )
    
    URUN_KATEGORI = (
        ('kereste', 'Kereste'),
        ('tomruk', 'Tomruk'),
        ('planya', 'Planya Kereste'),
        ('kurutulmus', 'Kurutulmuş Kereste'),
        ('mobilya', 'Mobilyalık Kereste'),
        ('insaat', 'İnşaat Kerestesi'),
        ('kontrplak', 'Kontrplak'),
        ('sunta', 'Sunta'),
        ('mdf', 'MDF'),
        ('osb', 'OSB'),
        ('yonga', 'Yonga'),
        ('talas', 'Talaş'),
        ('kabuk', 'Kabuk'),
        ('pelet', 'Pelet'),
        ('briket', 'Briket'),
        ('diger', 'Diğer'),
    )
    
    urun_kodu = models.CharField(max_length=50, unique=True, verbose_name="Ürün Kodu")
    urun_adi = models.CharField(max_length=200, verbose_name="Ürün Adı")
    urun_tipi = models.CharField(max_length=20, choices=URUN_TIPI, default='hammadde', verbose_name="Ürün Tipi")
    kategori = models.CharField(max_length=20, choices=URUN_KATEGORI, blank=True, verbose_name="Kategori")
    cins = models.CharField(max_length=100, verbose_name="Cins/Sınıf", blank=True)
    
    nace_kodu = models.ForeignKey(
        'NACEKodu',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="NACE Kodu",
        help_text="Ürünün NACE sınıflandırma kodu (TÜİK)"
    )
    
    mevcut_miktar = models.FloatField(default=0, verbose_name="Mevcut Miktar (m³)")
    toplam_giren = models.FloatField(default=0, verbose_name="Toplam Giren (m³)")
    toplam_cikan = models.FloatField(default=0, verbose_name="Toplam Çıkan (m³)")
    birim = models.CharField(max_length=20, default='m³', verbose_name="Birim")
    birim_fiyat = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Birim Fiyat (TL)")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    gelis_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    stokta_mi = models.BooleanField(default=True, verbose_name="Stokta Var mı?")
    
    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['urun_tipi', 'urun_adi']
    
    def __str__(self):
        nace = f" ({self.nace_kodu.kod})" if self.nace_kodu else ""
        return f"{self.urun_kodu} - {self.urun_adi}{nace} ({self.mevcut_miktar} {self.birim})"
    
    def stok_ekle(self, miktar):
        self.mevcut_miktar += miktar
        self.toplam_giren += miktar
        self.save()
    
    def stok_cikar(self, miktar):
        if self.mevcut_miktar >= miktar:
            self.mevcut_miktar -= miktar
            self.toplam_cikan += miktar
            self.save()
            return True
        return False


# ==================== İHALE ====================
class Ihale(models.Model):
    DURUM_CHOICES = (
        ('devam_ediyor', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    )
    
    ODEME_DURUMU_CHOICES = (
        ('odenmedi', 'Ödenmedi'),
        ('kismi_odendi', 'Kısmi Ödendi'),
        ('tamamen_odendi', 'Tamamen Ödendi'),
    )

    kik_no = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="KİK İhale No",
        help_text="Kamu İhale Kurumu tarafından verilen ihale numarası (opsiyonel)"
    )

    sistem_ihale_no = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        editable=False,
        verbose_name="Sistem İhale No"
    )

    tedarikci = models.ForeignKey(
        'Tedarikci', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tedarikçi"
    )
    urun_adi = models.CharField(max_length=200, verbose_name="Ürün Adı")
    
    alis_tarihi = models.DateField(null=True, blank=True, verbose_name="Alış Tarihi")
    parti_no = models.CharField(max_length=50, blank=True, verbose_name="Parti Numarası")
    istif_no = models.CharField(max_length=200, blank=True, verbose_name="İstif No")
    boy = models.CharField(max_length=100, blank=True, verbose_name="Boy")
    
    toplam_ihale_miktari = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0, 
        verbose_name="Parti Miktarı (m³)"
    )
    kalan_miktar = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0, 
        verbose_name="Kalan Miktar (m³)"
    )
    toplam_adet = models.IntegerField(default=0, verbose_name="Parti Adet")
    kalan_adet = models.IntegerField(default=0, verbose_name="Kalan Adet")
    
    birim_fiyat = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0,
        verbose_name="Birim Fiyat (TL)"
    )
    toplam_tutar = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0, 
        verbose_name="Toplam Tutar"
    )
    
    durum = models.CharField(
        max_length=20, 
        choices=DURUM_CHOICES, 
        default='devam_ediyor', 
        verbose_name="Durum"
    )
    odeme_durumu = models.CharField(
        max_length=20, 
        choices=ODEME_DURUMU_CHOICES, 
        default='odenmedi', 
        verbose_name="Ödeme Durumu"
    )
    
    ihale_tarihi = models.DateField(auto_now_add=True, verbose_name="Kayıt Tarihi")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "İhale"
        verbose_name_plural = "İhaleler"
        ordering = ['sistem_ihale_no', 'parti_no']

    def save(self, *args, **kwargs):
        from decimal import Decimal, getcontext, InvalidOperation
        from django.db import models as django_models
        import logging
        
        getcontext().prec = 28
        logger = logging.getLogger(__name__)
        
        if not self.sistem_ihale_no:
            son_kayit = Ihale.objects.all().order_by('id').last()
            if son_kayit and son_kayit.sistem_ihale_no:
                try:
                    son_sayi = int(son_kayit.sistem_ihale_no.split('-')[1])
                    yeni_sayi = son_sayi + 1
                except (ValueError, IndexError):
                    yeni_sayi = 1
            else:
                yeni_sayi = 1
            self.sistem_ihale_no = f"IHA-{yeni_sayi:04d}"

        if not self.alis_tarihi:
            self.alis_tarihi = self.ihale_tarihi

        try:
            if self.toplam_ihale_miktari is None:
                miktar_decimal = Decimal('0')
            elif isinstance(self.toplam_ihale_miktari, Decimal):
                miktar_decimal = self.toplam_ihale_miktari
            else:
                miktar_decimal = Decimal(str(self.toplam_ihale_miktari))
            
            if self.birim_fiyat is None:
                fiyat_decimal = Decimal('0')
            elif isinstance(self.birim_fiyat, Decimal):
                fiyat_decimal = self.birim_fiyat
            else:
                fiyat_decimal = Decimal(str(self.birim_fiyat))
            
            hesaplanan = miktar_decimal * fiyat_decimal
            self.toplam_tutar = hesaplanan.quantize(Decimal('0.0001'))
            logger.debug(f"Toplam tutar hesaplandı: {self.toplam_tutar}")
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"❌ Toplam tutar hesaplama hatası: {e}")
            self.toplam_tutar = Decimal('0')
        
        super().save(*args, **kwargs)
        
        try:
            sevk_toplam = self.sevkler.aggregate(
                toplam_miktar=django_models.Sum('sevk_miktar'),
                toplam_adet=django_models.Sum('sevk_adet')
            )
            toplam_gelen = sevk_toplam['toplam_miktar'] or Decimal('0')
            toplam_gelen_adet = sevk_toplam['toplam_adet'] or 0
        except Exception:
            toplam_gelen = Decimal('0')
            toplam_gelen_adet = 0
        
        toplam_miktar_dec = Decimal(str(self.toplam_ihale_miktari or 0))
        kalan_miktar = toplam_miktar_dec - toplam_gelen
        kalan_adet = (self.toplam_adet or 0) - toplam_gelen_adet
        
        if kalan_miktar < 0:
            kalan_miktar = Decimal('0')
        if kalan_adet < 0:
            kalan_adet = 0
        
        kalan_miktar = round(kalan_miktar, 4)
        
        yeni_durum = self.durum
        if self.durum != 'iptal':
            if kalan_miktar == 0 and kalan_adet == 0:
                if self.toplam_ihale_miktari > 0 or self.toplam_adet > 0:
                    yeni_durum = 'tamamlandi'
            else:
                yeni_durum = 'devam_ediyor'
        
        kalan_degisti = (self.kalan_miktar != kalan_miktar or self.kalan_adet != kalan_adet)
        durum_degisti = (self.durum != yeni_durum)
        
        if kalan_degisti or durum_degisti:
            Ihale.objects.filter(pk=self.pk).update(
                kalan_miktar=kalan_miktar,
                kalan_adet=kalan_adet,
                durum=yeni_durum
            )
            self.kalan_miktar = kalan_miktar
            self.kalan_adet = kalan_adet
            self.durum = yeni_durum
    
    def update_kalan(self):
        """Sevklerden kalan miktarı güncelle + durumu otomatik ayarla"""
        from django.db import models
        from decimal import Decimal, getcontext
        
        getcontext().prec = 28
        
        sevk_sonuclari = self.sevkler.aggregate(
            toplam_gelen=models.Sum('sevk_miktar'),
            toplam_gelen_adet=models.Sum('sevk_adet')
        )
        
        toplam_gelen = sevk_sonuclari['toplam_gelen'] or Decimal('0')
        toplam_gelen_adet = sevk_sonuclari['toplam_gelen_adet'] or 0
        
        kalan_miktar = Decimal(str(self.toplam_ihale_miktari)) - Decimal(str(toplam_gelen))
        kalan_adet = self.toplam_adet - toplam_gelen_adet
        
        if kalan_miktar < 0:
            kalan_miktar = Decimal('0')
        if kalan_adet < 0:
            kalan_adet = 0
        
        self.kalan_miktar = round(kalan_miktar, 4)
        self.kalan_adet = kalan_adet
        
        if self.durum != 'iptal':
            if self.kalan_miktar == 0 and self.kalan_adet == 0:
                if self.toplam_ihale_miktari > 0 or self.toplam_adet > 0:
                    self.durum = 'tamamlandi'
            else:
                self.durum = 'devam_ediyor'
        
        self.save(update_fields=['kalan_miktar', 'kalan_adet', 'durum'])

    def __str__(self):
        tedarikci_unvan = self.tedarikci.unvan if self.tedarikci else "BELİRSİZ TEDARİKÇİ"
        return f"{self.sistem_ihale_no} - {self.parti_no} ({tedarikci_unvan})"
    
    @property
    def toplam_gelen_miktar(self):
        return self.sevkler.aggregate(toplam=models.Sum('sevk_miktar'))['toplam'] or 0
    
    @property
    def toplam_gelen_adet(self):
        return self.sevkler.aggregate(toplam=models.Sum('sevk_adet'))['toplam'] or 0


# ==================== İHALE SEVK ====================
class IhaleSevk(models.Model):
    """
    İhale Partisine ait sevkler - Her sevk stoğa giriş olarak işlenir
    
    NOT: Ödeme durumu PARTİ bazlıdır (Ihale.odeme_durumu).
    Sevk bazlı sadece TAŞIMA ödemesi vardır.
    Taşıma ödemesi TasiyiciOdeme modelinde takip edilir.
    """
    
    ihale = models.ForeignKey(Ihale, on_delete=models.CASCADE, related_name='sevkler', verbose_name="İhale")
    
    # ===== SEVK BİLGİLERİ =====
    sevk_tarihi = models.DateField(verbose_name="Sevk Tarihi")
    sevk_miktar = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0, 
        verbose_name="Sevk Miktarı (m³)"
    )
    sevk_adet = models.IntegerField(default=0, verbose_name="Sevk Adeti")
    
    # ===== TAŞIYICI BİLGİLERİ =====
    tasiyici = models.ForeignKey(
        'Tasiyici',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sevkler',
        verbose_name="Taşıyıcı"
    )
    tasiyici_arac = models.ForeignKey(
        'TasiyiciArac',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sevkler',
        verbose_name="Araç"
    )
    
    # ===== SEVK DETAY =====
    irsaliye_no = models.CharField(
        max_length=50, blank=True, verbose_name="İrsaliye No"
    )
    nereden = models.CharField(
        max_length=200, blank=True, verbose_name="Nereden (Depo/OİM)"
    )
    nereye = models.CharField(
        max_length=200, blank=True, verbose_name="Nereye"
    )
    
    # ===== FATURA BİLGİLERİ =====
    fatura_no = models.CharField(
        max_length=50, blank=True, verbose_name="Fatura No"
    )
    fatura_tarihi = models.DateField(
        null=True, blank=True, verbose_name="Fatura Tarihi"
    )
    tasima_birim_fiyat = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Taşıma Birim Fiyatı (TL/m³)"
    )
    tasima_toplam_tutar = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Taşıma Toplam Tutar (TL)"
    )
    
    # ===== TAŞIMA ÖDEME DURUMU (Otomatik hesaplanır) =====
    ODEME_DURUMU_CHOICES = (
        ('odenmedi', 'Ödenmedi'),
        ('kismi_odendi', 'Kısmi Ödendi'),
        ('tamamen_odendi', 'Tamamen Ödendi'),
    )
    tasima_odeme_durumu = models.CharField(
        max_length=20,
        choices=ODEME_DURUMU_CHOICES,
        default='odenmedi',
        verbose_name="Taşıma Ödeme Durumu",
        help_text="Otomatik hesaplanır (TasiyiciOdeme kayıtlarından)"
    )
    tasima_odenen_tutar = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name="Taşımaya Ödenen (TL)",
        help_text="Otomatik hesaplanır (TasiyiciOdeme toplamı)"
    )
    
    # ===== KALAN MİKTAR (Otomatik hesaplanır) =====
    kalan_miktar = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        default=0, 
        verbose_name="Kalan Miktar (m³)"
    )
    kalan_adet = models.IntegerField(default=0, verbose_name="Kalan Adet")
    
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "İhale Sevki"
        verbose_name_plural = "İhale Sevkleri"
        ordering = ['-sevk_tarihi']
    
    def _tasima_odeme_guncelle(self):
        """TasiyiciOdeme kayıtlarından taşıma ödeme durumunu hesapla."""
        from decimal import Decimal
        from django.db import models as django_models
        
        if not self.pk:
            toplam_odenen = Decimal('0')
        else:
            toplam_odenen = self.odemeler.aggregate(
                toplam=django_models.Sum('odeme_tutari')
            )['toplam'] or Decimal('0')
        
        self.tasima_odenen_tutar = toplam_odenen
        
        if self.tasima_toplam_tutar and self.tasima_toplam_tutar > 0:
            if toplam_odenen >= self.tasima_toplam_tutar:
                self.tasima_odeme_durumu = 'tamamen_odendi'
            elif toplam_odenen > 0:
                self.tasima_odeme_durumu = 'kismi_odendi'
            else:
                self.tasima_odeme_durumu = 'odenmedi'
        else:
            self.tasima_odeme_durumu = 'odenmedi'
    
    def guncelle_tasima_odeme_durumu(self):
        """TasiyiciOdeme save/delete sonrası çağrılır."""
        self._tasima_odeme_guncelle()
        IhaleSevk.objects.filter(pk=self.pk).update(
            tasima_odeme_durumu=self.tasima_odeme_durumu,
            tasima_odenen_tutar=self.tasima_odenen_tutar,
        )
    
    def save(self, *args, **kwargs):
        from decimal import Decimal, getcontext, InvalidOperation
        from django.db import models as django_models
        
        try:
            getcontext().prec = 28
            is_new = self.pk is None
            
            sevk_miktar_str = str(self.sevk_miktar) if self.sevk_miktar is not None else '0'
            sevk_miktar_decimal = Decimal(sevk_miktar_str)
            self.sevk_miktar = round(sevk_miktar_decimal, 4)
            
            if self.tasima_birim_fiyat and self.sevk_miktar:
                self.tasima_toplam_tutar = round(
                    Decimal(str(self.sevk_miktar)) * Decimal(str(self.tasima_birim_fiyat)), 2
                )
            
            self._tasima_odeme_guncelle()
            
            if is_new:
                toplam_sevk = self.ihale.sevkler.aggregate(
                    toplam=django_models.Sum('sevk_miktar')
                )['toplam'] or Decimal('0')
                toplam_sevk_adet = self.ihale.sevkler.aggregate(
                    toplam=django_models.Sum('sevk_adet')
                )['toplam'] or 0
            else:
                toplam_sevk = self.ihale.sevkler.exclude(id=self.id).aggregate(
                    toplam=django_models.Sum('sevk_miktar')
                )['toplam'] or Decimal('0')
                toplam_sevk_adet = self.ihale.sevkler.exclude(id=self.id).aggregate(
                    toplam=django_models.Sum('sevk_adet')
                )['toplam'] or 0
            
            yeni_toplam_sevk = toplam_sevk + Decimal(str(self.sevk_miktar))
            yeni_toplam_sevk_adet = toplam_sevk_adet + self.sevk_adet
            
            toplam_miktar_str = str(self.ihale.toplam_ihale_miktari) if self.ihale.toplam_ihale_miktari is not None else '0'
            toplam_miktar_decimal = Decimal(toplam_miktar_str)
            kalan = toplam_miktar_decimal - yeni_toplam_sevk
            self.kalan_miktar = round(kalan, 4) if kalan > 0 else Decimal('0')
            self.kalan_adet = self.ihale.toplam_adet - yeni_toplam_sevk_adet
            if self.kalan_adet < 0:
                self.kalan_adet = 0
            
            super().save(*args, **kwargs)
            
            if self.ihale:
                self.ihale.update_kalan()
            
            if is_new and self.sevk_miktar > 0:
                self._create_stok_hareketi()
        except (InvalidOperation, ValueError, TypeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ IhaleSevk.save hatası: {type(e).__name__}: {e}")
            self.kalan_miktar = Decimal('0')
            self.kalan_adet = 0
            super().save(*args, **kwargs)
    
    def _create_stok_hareketi(self):
        """Stok hareketi oluştur"""
        from decimal import Decimal
        
        try:
            urun = Urun.objects.get(urun_adi__icontains=self.ihale.urun_adi)
        except Urun.DoesNotExist:
            urun = Urun.objects.create(
                urun_kodu=f"HRM-{self.ihale.id}-{self.ihale.parti_no}",
                urun_adi=self.ihale.urun_adi,
                urun_tipi='hammadde',
                cins="Standart",
                mevcut_miktar=0,
                birim="m³"
            )
        except Urun.MultipleObjectsReturned:
            urun = Urun.objects.filter(urun_adi__icontains=self.ihale.urun_adi).first()
        
        StokHareket.objects.create(
            urun=urun,
            ihale=self.ihale,
            ihale_sevk=self,
            hareket_tipi='ihale_giris',
            miktar=float(self.sevk_miktar),
            birim_fiyat=self.ihale.birim_fiyat,
            toplam_tutar=Decimal(str(self.sevk_miktar)) * self.ihale.birim_fiyat,
            aciklama=f"{self.ihale.sistem_ihale_no} - Parti {self.ihale.parti_no} - Sevk {self.id}",
            kullanici=None
        )
        
        urun.stok_ekle(float(self.sevk_miktar))
    
    def delete(self, *args, **kwargs):
        """
        Sevk silindiğinde:
        1. İlişkili stok hareketlerini ÖNCE sil (SET_NULL tetiklenmeden!)
        2. Ürün stoğunu geri düş
        3. İhale kalanını güncelle
        """
        import logging
        logger = logging.getLogger(__name__)
        
        ihale = self.ihale
        sevk_miktar = self.sevk_miktar
        sevk_id = self.id
        
        # ADIM 1: İLİŞKİLİ HAREKETLERİ LİSTELE (SİLME!)
        iliskili_hareketler = list(StokHareket.objects.filter(ihale_sevk_id=sevk_id))
        silinen_hareket_sayisi = len(iliskili_hareketler)
        
        logger.info(f"🔍 Sevk {sevk_id} için {silinen_hareket_sayisi} stok hareketi bulundu")
        
        # ADIM 2: ÜRÜN STOĞUNU GERİ DÜŞ
        for hareket in iliskili_hareketler:
            try:
                urun = hareket.urun
                urun.mevcut_miktar -= hareket.miktar
                urun.toplam_giren -= hareket.miktar
                urun.save(update_fields=['mevcut_miktar', 'toplam_giren'])
                
                logger.info(
                    f"↩️  Stok geri düşüldü: {urun.urun_adi} "
                    f"(-{hareket.miktar} m³) → {urun.mevcut_miktar} m³"
                )
            except Exception as e:
                logger.error(f"❌ Stok geri düşme hatası: {type(e).__name__}: {e}")
        
        # ADIM 3: STOK HAREKETLERİNİ SİL (Sevki silmeden ÖNCE!)
        if iliskili_hareketler:
            ids = [h.id for h in iliskili_hareketler]
            StokHareket.objects.filter(id__in=ids).delete()
            logger.info(f"🗑️  {silinen_hareket_sayisi} stok hareketi silindi")
        
        # ADIM 4: SEVKİ SİL (EN SON!)
        super().delete(*args, **kwargs)
        
        # ADIM 5: İHALE KALANINI GÜNCELLE
        if ihale:
            try:
                ihale.refresh_from_db()
                ihale.update_kalan()
                ihale.refresh_from_db()
                
                if ihale.durum != 'iptal':
                    if ihale.kalan_miktar == 0 and ihale.kalan_adet == 0:
                        if ihale.toplam_ihale_miktari > 0 or ihale.toplam_adet > 0:
                            ihale.durum = 'tamamlandi'
                    else:
                        ihale.durum = 'devam_ediyor'
                    ihale.save(update_fields=['durum'])
            except Exception as e:
                logger.error(f"❌ İhale güncelleme hatası: {type(e).__name__}: {e}")
        
        logger.info(
            f"🗑️  Sevk silindi: ID={sevk_id}, Miktar={sevk_miktar} m³, "
            f"Silinen stok hareketi: {silinen_hareket_sayisi}"
        )
    
    def __str__(self):
        tasiyici_adi = self.tasiyici.ad if self.tasiyici else "Taşıyıcı Yok"
        return f"{self.ihale.sistem_ihale_no} - Parti {self.ihale.parti_no} - Sevk {self.id} ({self.sevk_miktar}m³) - {tasiyici_adi}"


# ==================== STOK HAREKET ====================
class StokHareket(models.Model):
    HAREKET_TIPI = (
        ('ihale_giris', 'İhale Giriş'),
        ('sahis_alim', 'Şahıs Alım'),
        ('uretim_giris', 'Üretim Giriş'),
        ('siparis_cikis', 'Sipariş Çıkış'),
        ('fire', 'Fire/Zayiat'),
        ('iade', 'İade'),
        ('hammadde_cikis', 'Hammadde Çıkış (Üretime)'),
        ('mamul_giris', 'Mamul Giriş'),
        ('mamul_cikis', 'Mamul Çıkış'),
    )
    
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    ihale = models.ForeignKey(Ihale, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İhale")
    ihale_sevk = models.ForeignKey(IhaleSevk, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İhale Sevki")
    uretim = models.ForeignKey('Uretim', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Üretim")
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    miktar = models.FloatField(verbose_name="Miktar (m³)")
    birim_fiyat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Birim Fiyat")
    toplam_tutar = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        editable=False,
        verbose_name="Toplam Tutar"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan")
    
    class Meta:
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ['-tarih']
    
    def save(self, *args, **kwargs):
        if self.miktar and self.birim_fiyat:
            self.toplam_tutar = Decimal(str(self.miktar)) * self.birim_fiyat
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_hareket_tipi_display()} - {self.urun} - {self.miktar}m³"


# ==================== ÜRETİM REÇETESİ ====================
class UretimRecete(models.Model):
    recete_kodu = models.CharField(max_length=50, unique=True, verbose_name="Reçete Kodu")
    recete_adi = models.CharField(max_length=200, verbose_name="Reçete Adı")
    hammadde = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='recete_hammadde', verbose_name="Hammadde")
    hammadde_miktar = models.FloatField(verbose_name="Hammadde Miktarı (m³)")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Üretim Reçetesi"
        verbose_name_plural = "Üretim Reçeteleri"
    
    def __str__(self):
        return f"{self.recete_kodu} - {self.recete_adi}"


# ==================== ÜRETİM REÇETE DETAY ====================
class UretimReceteDetay(models.Model):
    recete = models.ForeignKey(UretimRecete, on_delete=models.CASCADE, related_name='detaylar', verbose_name="Reçete")
    mamul = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Mamul Ürün")
    verim_orani = models.FloatField(verbose_name="Verim Oranı (%)")
    miktar = models.FloatField(verbose_name="Çıkan Miktar (m³)")
    birim = models.CharField(max_length=20, default='m³', verbose_name="Birim")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Reçete Detayı"
        verbose_name_plural = "Reçete Detayları"
    
    def __str__(self):
        return f"{self.recete.recete_kodu} - {self.mamul.urun_adi} (%{self.verim_orani})"


# ==================== ÜRETİM ====================
class Uretim(models.Model):
    DURUM_CHOICES = (
        ('planlandi', 'Planlandı'),
        ('devam_ediyor', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    )
    
    uretim_no = models.CharField(max_length=50, unique=True, verbose_name="Üretim No")
    recete = models.ForeignKey(UretimRecete, on_delete=models.CASCADE, verbose_name="Reçete")
    hammadde = models.ForeignKey(Urun, on_delete=models.CASCADE, related_name='uretim_hammadde', verbose_name="Hammadde")
    kullanilan_miktar = models.FloatField(verbose_name="Kullanılan Hammadde (m³)")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='planlandi', verbose_name="Durum")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Üretim"
        verbose_name_plural = "Üretimler"
        ordering = ['-baslangic_tarihi']
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            hammadde_urun = self.hammadde
            if hammadde_urun.stok_cikar(self.kullanilan_miktar):
                StokHareket.objects.create(
                    urun=hammadde_urun,
                    uretim=self,
                    hareket_tipi='hammadde_cikis',
                    miktar=self.kullanilan_miktar,
                    birim_fiyat=hammadde_urun.birim_fiyat or 0,
                    toplam_tutar=Decimal(str(self.kullanilan_miktar)) * (hammadde_urun.birim_fiyat or 0),
                    aciklama=f"Üretim {self.uretim_no} - Hammadde çıkışı",
                    kullanici=self.olusturan
                )
            
            for detay in self.recete.detaylar.all():
                mamul_urun = detay.mamul
                cikan_miktar = (self.kullanilan_miktar * detay.verim_orani) / 100
                mamul_urun.stok_ekle(cikan_miktar)
                
                StokHareket.objects.create(
                    urun=mamul_urun,
                    uretim=self,
                    hareket_tipi='mamul_giris',
                    miktar=cikan_miktar,
                    birim_fiyat=mamul_urun.birim_fiyat or 0,
                    toplam_tutar=Decimal(str(cikan_miktar)) * (mamul_urun.birim_fiyat or 0),
                    aciklama=f"Üretim {self.uretim_no} - {mamul_urun.urun_adi} girişi",
                    kullanici=self.olusturan
                )
    
    def __str__(self):
        return f"{self.uretim_no} - {self.recete.recete_adi}"


# ==================== FİRE ====================
class Fire(models.Model):
    FIRE_TIPI = (
        ('uretim', 'Üretim Fire'),
        ('depolama', 'Depolama Fire'),
        ('nakliye', 'Nakliye Fire'),
    )
    
    uretim = models.ForeignKey(Uretim, on_delete=models.CASCADE, verbose_name="Üretim")
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    fire_miktar = models.FloatField(verbose_name="Fire Miktarı (m³)")
    fire_tipi = models.CharField(max_length=20, choices=FIRE_TIPI, default='uretim', verbose_name="Fire Tipi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    class Meta:
        verbose_name = "Fire"
        verbose_name_plural = "Fireler"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.urun.stok_cikar(self.fire_miktar)
            StokHareket.objects.create(
                urun=self.urun,
                uretim=self.uretim,
                hareket_tipi='fire',
                miktar=self.fire_miktar,
                birim_fiyat=0,
                toplam_tutar=0,
                aciklama=f"Fire - {self.fire_tipi} - {self.aciklama}",
                kullanici=None
            )
    
    def __str__(self):
        return f"{self.uretim.uretim_no} - {self.urun.urun_adi} - {self.fire_miktar}m³"


# ==================== DEPO ====================
class Depo(models.Model):
    kod = models.CharField(max_length=50, unique=True, verbose_name="Depo Kodu")
    ad = models.CharField(max_length=200, verbose_name="Depo Adı")
    adres = models.TextField(blank=True, verbose_name="Adres")
    telefon = models.CharField(max_length=15, blank=True, verbose_name="Telefon")
    yetkili = models.CharField(max_length=100, blank=True, verbose_name="Yetkili")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    
    class Meta:
        verbose_name = "Depo"
        verbose_name_plural = "Depolar"
    
    def __str__(self):
        return f"{self.kod} - {self.ad}"


# ==================== RAF ====================
class Raf(models.Model):
    depo = models.ForeignKey(Depo, on_delete=models.CASCADE, related_name='raflar', verbose_name="Depo")
    kod = models.CharField(max_length=50, verbose_name="Raf Kodu")
    kapasite = models.FloatField(verbose_name="Kapasite (m³)", null=True, blank=True)
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Raf"
        verbose_name_plural = "Raflar"
        unique_together = ['depo', 'kod']
    
    def __str__(self):
        return f"{self.depo.kod} - {self.kod}"


# ==================== BARKOD ====================
class StokBarkod(models.Model):
    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    depo = models.ForeignKey(Depo, on_delete=models.CASCADE, verbose_name="Depo")
    raf = models.ForeignKey(Raf, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Raf")
    barkod = models.CharField(max_length=100, unique=True, verbose_name="Barkod")
    miktar = models.FloatField(default=0, verbose_name="Miktar (m³)")
    lot_no = models.CharField(max_length=50, blank=True, verbose_name="Lot No")
    son_kullanma = models.DateField(null=True, blank=True, verbose_name="Son Kullanma")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Stok Barkodu"
        verbose_name_plural = "Stok Barkodları"
    
    def __str__(self):
        return f"{self.barkod} - {self.urun.urun_adi} ({self.miktar} m³)"


# ==================== MAKİNE ====================
class Makine(models.Model):
    DURUM_CHOICES = (
        ('calisiyor', 'Çalışıyor'),
        ('bakim', 'Bakımda'),
        ('arizali', 'Arızalı'),
        ('dolu', 'Dolu (Üretimde)'),
    )
    
    kod = models.CharField(max_length=50, unique=True, verbose_name="Makine Kodu")
    ad = models.CharField(max_length=200, verbose_name="Makine Adı")
    model = models.CharField(max_length=100, blank=True, verbose_name="Model")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='calisiyor', verbose_name="Durum")
    saatlik_kapasite = models.FloatField(verbose_name="Saatlik Kapasite (m³)")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Makine"
        verbose_name_plural = "Makineler"
    
    def __str__(self):
        return f"{self.kod} - {self.ad} ({self.get_durum_display()})"


# ==================== ÜRETİM AŞAMASI ====================
class UretimAsama(models.Model):
    ASAMA_TIPI = (
        ('bekleme', 'Bekleme'),
        ('kesim', 'Kesim'),
        ('kurutma', 'Kurutma'),
        ('zımparalama', 'Zımparalama'),
        ('boyama', 'Boyama'),
        ('montaj', 'Montaj'),
        ('paketleme', 'Paketleme'),
        ('kalite', 'Kalite Kontrol'),
    )
    
    recete = models.ForeignKey(UretimRecete, on_delete=models.CASCADE, related_name='asamalar', verbose_name="Reçete")
    asama_tipi = models.CharField(max_length=20, choices=ASAMA_TIPI, verbose_name="Aşama Tipi")
    siralama = models.IntegerField(verbose_name="Sıralama")
    tahmini_sure = models.FloatField(verbose_name="Tahmini Süre (Saat)")
    makine = models.ForeignKey(Makine, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Makine")
    isci_sayisi = models.IntegerField(default=1, verbose_name="Gerekli İşçi Sayısı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Üretim Aşaması"
        verbose_name_plural = "Üretim Aşamaları"
        ordering = ['siralama']
    
    def __str__(self):
        return f"{self.recete.recete_kodu} - {self.get_asama_tipi_display()}"


# ==================== ÜRETİM EMRİ ====================
class UretimEmri(models.Model):
    DURUM_CHOICES = (
        ('planlandi', 'Planlandı'),
        ('devam', 'Devam Ediyor'),
        ('tamamlandi', 'Tamamlandı'),
        ('iptal', 'İptal'),
    )
    
    emir_no = models.CharField(max_length=50, unique=True, verbose_name="Emir No")
    recete = models.ForeignKey(UretimRecete, on_delete=models.CASCADE, verbose_name="Reçete")
    hammadde = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Hammadde")
    hedef_miktar = models.FloatField(verbose_name="Hedef Miktar (m³)")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='planlandi', verbose_name="Durum")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Üretim Emri"
        verbose_name_plural = "Üretim Emirleri"
        ordering = ['-baslangic_tarihi']
    
    def __str__(self):
        return f"{self.emir_no} - {self.recete.recete_adi}"


# ==================== AŞAMA TAKİBİ ====================
class UretimAsamaTakip(models.Model):
    DURUM_CHOICES = (
        ('bekliyor', 'Bekliyor'),
        ('devam', 'Devam Ediyor'),
        ('tamam', 'Tamamlandı'),
        ('hata', 'Hata/Durduruldu'),
    )
    
    emir = models.ForeignKey(UretimEmri, on_delete=models.CASCADE, related_name='asama_takip', verbose_name="Üretim Emri")
    asama = models.ForeignKey(UretimAsama, on_delete=models.CASCADE, verbose_name="Aşama")
    baslangic_tarihi = models.DateTimeField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='bekliyor', verbose_name="Durum")
    calisan = models.ForeignKey('personel.Personel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Çalışan")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Aşama Takibi"
        verbose_name_plural = "Aşama Takipleri"
    
    def __str__(self):
        return f"{self.emir.emir_no} - {self.asama.get_asama_tipi_display()}"


# ==================== TAŞIYICI ====================
class Tasiyici(models.Model):
    """Taşıyıcı firma/şahıs ve araç bilgileri"""
    TIP_CHOICES = (
        ('firma', 'Firma'),
        ('sahis', 'Şahıs'),
        ('kooperatif', 'Kooperatif'),
    )
    
    kod = models.CharField(
        max_length=50, unique=True, blank=True, editable=False,
        verbose_name="Taşıyıcı Kodu"
    )
    ad = models.CharField(max_length=200, verbose_name="Firma/Şahıs Adı")
    tipi = models.CharField(
        max_length=20, choices=TIP_CHOICES, default='firma',
        verbose_name="Tipi"
    )
    yetkili = models.CharField(max_length=100, blank=True, verbose_name="Yetkili Kişi")
    telefon = models.CharField(max_length=15, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, verbose_name="Adres")
    vergi_dairesi = models.CharField(max_length=100, blank=True, verbose_name="Vergi Dairesi")
    vergi_no = models.CharField(max_length=20, blank=True, verbose_name="Vergi No")
    iban = models.CharField(max_length=34, blank=True, verbose_name="IBAN")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Taşıyıcı"
        verbose_name_plural = "Taşıyıcılar"
        ordering = ['ad']
    
    def __str__(self):
        return f"{self.kod} - {self.ad}"
    
    def save(self, *args, **kwargs):
        if not self.kod:
            son = Tasiyici.objects.all().order_by('id').last()
            if son and son.kod:
                try:
                    son_sayi = int(son.kod.split('-')[1])
                    yeni = son_sayi + 1
                except (ValueError, IndexError):
                    yeni = 1
            else:
                yeni = 1
            self.kod = f"TAS-{yeni:04d}"
        super().save(*args, **kwargs)


# ==================== TAŞIYICI ARACI ====================
class TasiyiciArac(models.Model):
    """Taşıyıcıya ait araç/kamyon bilgileri"""
    tasiyici = models.ForeignKey(
        Tasiyici, on_delete=models.CASCADE, related_name='araclar',
        verbose_name="Taşıyıcı"
    )
    plaka = models.CharField(max_length=50, verbose_name="Plaka")
    arac_tipi = models.CharField(max_length=100, blank=True, verbose_name="Araç Tipi")
    marka = models.CharField(max_length=100, blank=True, verbose_name="Marka")
    model = models.CharField(max_length=100, blank=True, verbose_name="Model")
    kapasite_m3 = models.FloatField(null=True, blank=True, verbose_name="Kapasite (m³)")
    sofor_adi = models.CharField(max_length=100, blank=True, verbose_name="Şoför Adı")
    sofor_telefon = models.CharField(max_length=15, blank=True, verbose_name="Şoför Telefon")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    class Meta:
        verbose_name = "Taşıyıcı Aracı"
        verbose_name_plural = "Taşıyıcı Araçları"
        unique_together = ['tasiyici', 'plaka']
    
    def __str__(self):
        return f"{self.plaka} - {self.tasiyici.ad}"


# ==================== TAŞIYICI ÖDEME ====================
class TasiyiciOdeme(models.Model):
    """Taşıyıcıya yapılan ödemeler (sevk bazlı, taşıma hizmeti için)"""
    ODEME_TIPI = (
        ('nakit', 'Nakit'),
        ('havale', 'Havale/EFT'),
        ('cek', 'Çek'),
        ('senet', 'Senet'),
    )
    
    sevk = models.ForeignKey(
        IhaleSevk, on_delete=models.CASCADE,
        related_name='odemeler',
        verbose_name="İhale Sevki"
    )
    odeme_tarihi = models.DateField(verbose_name="Ödeme Tarihi")
    odeme_tutari = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name="Ödeme Tutarı (TL)"
    )
    odeme_tipi = models.CharField(
        max_length=20, choices=ODEME_TIPI, default='havale',
        verbose_name="Ödeme Tipi"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Taşıyıcı Ödemesi"
        verbose_name_plural = "Taşıyıcı Ödemeleri"
        ordering = ['-odeme_tarihi']
    
    def __str__(self):
        tasiyici_adi = self.sevk.tasiyici.ad if self.sevk and self.sevk.tasiyici else '?'
        return f"{tasiyici_adi} - {self.odeme_tutari} TL - {self.odeme_tarihi}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sevkin taşıma ödeme durumunu güncelle
        if self.sevk:
            self.sevk.guncelle_tasima_odeme_durumu()
    
    def delete(self, *args, **kwargs):
        sevk = self.sevk
        super().delete(*args, **kwargs)
        # Sevkin taşıma ödeme durumunu güncelle
        if sevk:
            sevk.guncelle_tasima_odeme_durumu()


# ==================== STOK DEVİR ====================
class StokDevir(models.Model):
    """Her ay için manuel girilen devir miktarı"""
    AY_CHOICES = [
        (1, 'Ocak'), (2, 'Şubat'), (3, 'Mart'), (4, 'Nisan'),
        (5, 'Mayıs'), (6, 'Haziran'), (7, 'Temmuz'), (8, 'Ağustos'),
        (9, 'Eylül'), (10, 'Ekim'), (11, 'Kasım'), (12, 'Aralık'),
    ]
    
    yil = models.IntegerField(verbose_name="Yıl")
    ay = models.IntegerField(choices=AY_CHOICES, verbose_name="Ay")
    devir_miktar = models.DecimalField(
        max_digits=15, decimal_places=4, default=0,
        verbose_name="Devir Miktarı (m³)"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Oluşturan"
    )
    
    class Meta:
        verbose_name = "Stok Devir"
        verbose_name_plural = "Stok Devirleri"
        unique_together = ['yil', 'ay']
        ordering = ['-yil', '-ay']
    
    def __str__(self):
        ay_adi = dict(self.AY_CHOICES).get(self.ay, str(self.ay))
        return f"{ay_adi} {self.yil} → {self.devir_miktar} m³"
    
    @property
    def donem_etiketi(self):
        """Örn: 'Ekim 2026'"""
        ay_adi = dict(self.AY_CHOICES).get(self.ay, str(self.ay))
        return f"{ay_adi} {self.yil}"