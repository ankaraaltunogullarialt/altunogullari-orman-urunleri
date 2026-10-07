# stok/admin.py
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db import models
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta, datetime
from import_export import resources
from import_export import fields
from import_export.admin import ImportExportModelAdmin
from .models import (
    Urun, Tedarikci, TedarikciTipi, Ihale, IhaleSevk, 
    StokHareket, Depo, Raf, StokBarkod, Makine,
    UretimAsama, UretimEmri, UretimAsamaTakip,
    UretimRecete, UretimReceteDetay, Uretim, Fire,
    NACEKodu, Tasiyici, TasiyiciArac, TasiyiciOdeme, StokDevir,
)

class OdemeDurumuIhaleSevkFilter(SimpleListFilter):
    """Ödeme durumu filtresi - tüm seçenekler + kayıt sayısı"""
    title = 'Ödeme Durumu'
    parameter_name = 'odeme_durumu'
    
    def lookups(self, request, model_admin):
        from .models import IhaleSevk
        sonuc = []
        for kod, etiket in IhaleSevk.ODEME_DURUMU_CHOICES:
            adet = model_admin.get_queryset(request).filter(odeme_durumu=kod).count()
            sonuc.append((kod, f'{etiket} ({adet})'))
        return sonuc
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(odeme_durumu=self.value())
        return queryset


# ==================== ÖZEL FİLTRELER ====================
class TedarikciFilter(SimpleListFilter):
    title = 'Tedarikçi'
    parameter_name = 'tedarikci'
    
    def lookups(self, request, model_admin):
        return [(t.id, t.unvan) for t in Tedarikci.objects.all().order_by('unvan')]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tedarikci_id=self.value())
        return queryset


class StokHareketTedarikciFilter(SimpleListFilter):
    """StokHareket için tedarikçi filtresi (ihale üzerinden)"""
    title = 'Tedarikçi'
    parameter_name = 'tedarikci'

    def lookups(self, request, model_admin):
        tedarikciler = Tedarikci.objects.filter(
            ihale__isnull=False
        ).distinct().order_by('unvan')
        return [(t.id, t.unvan) for t in tedarikciler]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ihale__tedarikci_id=self.value())
        return queryset


# ==================== NACE KODU RESOURCE ====================
class NACEKoduResource(resources.ModelResource):
    class Meta:
        model = NACEKodu
        fields = ['kod', 'aciklama', 'sistem_kodu', 'aktif_mi']
        export_order = ['kod', 'aciklama', 'sistem_kodu', 'aktif_mi']
        import_id_fields = ['kod']
        skip_unchanged = True
        report_skipped = True


# ==================== ÜRÜN RESOURCE ====================
class UrunResource(resources.ModelResource):
    class Meta:
        model = Urun
        fields = [
            'urun_kodu', 'urun_adi', 'urun_tipi', 'kategori', 
            'cins', 'mevcut_miktar', 'birim', 'birim_fiyat', 
            'stokta_mi', 'aciklama'
        ]
        export_order = [
            'urun_kodu', 'urun_adi', 'urun_tipi', 'kategori', 
            'cins', 'mevcut_miktar', 'birim', 'birim_fiyat', 
            'stokta_mi', 'aciklama'
        ]
        import_id_fields = ['urun_kodu']
        skip_unchanged = True
        report_skipped = True


# ==================== TEDARİKÇİ RESOURCE ====================
class TedarikciResource(resources.ModelResource):
    class Meta:
        model = Tedarikci
        fields = ['kod', 'unvan', 'tedarikci_tipi', 'vergi_dairesi', 'vergi_no', 'telefon', 'adres', 'aktif_mi']
        export_order = ['kod', 'unvan', 'tedarikci_tipi', 'vergi_dairesi', 'vergi_no', 'telefon', 'adres', 'aktif_mi']
        import_id_fields = ['kod']
        skip_unchanged = True
        report_skipped = True


# ==================== İHALE RESOURCE ====================
class IhaleResource(resources.ModelResource):
    
    def dehydrate_tedarikci(self, ihale):
        if ihale.tedarikci:
            return ihale.tedarikci.unvan
        return ''
    
    def before_import_row(self, row, row_number=None, **kwargs):
        from .models import Tedarikci
        
        if not isinstance(row, dict):
            row = dict(row)
        
        tedarikci_adi = row.get('tedarikci', '')
        if not tedarikci_adi:
            tedarikci_adi = row.get('tedarikci__unvan', '')
        
        if tedarikci_adi and str(tedarikci_adi).strip():
            tedarikci_adi = str(tedarikci_adi).strip()
            tedarikci, created = Tedarikci.objects.get_or_create(
                unvan=tedarikci_adi,
                defaults={
                    'aktif_mi': True,
                    'aciklama': f'Excel import ile oluşturuldu - {tedarikci_adi}'
                }
            )
            row['tedarikci'] = tedarikci.id
        else:
            default_tedarikci, _ = Tedarikci.objects.get_or_create(
                unvan='BELİRSİZ TEDARİKÇİ',
                defaults={
                    'aktif_mi': True,
                    'aciklama': 'Sistem tarafından otomatik oluşturuldu'
                }
            )
            row['tedarikci'] = default_tedarikci.id
        
        kik_no = row.get('kik_no', '')
        if not kik_no or str(kik_no).strip() in ('', 'None'):
            row['kik_no'] = None
        
        sistem_no = row.get('sistem_ihale_no', '')
        if not sistem_no or str(sistem_no).strip() in ('', 'None'):
            row['sistem_ihale_no'] = None
        
        aciklama = row.get('aciklama', '')
        if not aciklama or str(aciklama).strip() in ('', 'None'):
            kik_no_val = row.get('kik_no', '')
            parti_no = row.get('parti_no', '')
            row['aciklama'] = f"Excel'den içe aktarıldı - {kik_no_val} - {parti_no}"
        else:
            row['aciklama'] = str(aciklama)
        
        durum = row.get('durum', 'devam_ediyor')
        durum_map = {
            'Devam Ediyor': 'devam_ediyor',
            'devam_ediyor': 'devam_ediyor',
            'Tamamlandı': 'tamamlandi',
            'tamamlandi': 'tamamlandi',
            'İptal': 'iptal',
            'iptal': 'iptal'
        }
        row['durum'] = durum_map.get(str(durum), 'devam_ediyor')
        
        odeme = row.get('odeme_durumu', 'odenmedi')
        odeme_map = {
            'ödendi': 'tamamen_odendi',
            'ödenmedi': 'odenmedi',
            'tamamen_odendi': 'tamamen_odendi',
            'tamamen_ödendi': 'tamamen_odendi',
            'kısmi': 'kismi_odendi',
            'kismi_odendi': 'kismi_odendi',
            'odenmedi': 'odenmedi'
        }
        row['odeme_durumu'] = odeme_map.get(str(odeme).lower(), 'odenmedi')
        
        birim_fiyat = row.get('birim_fiyat')
        if birim_fiyat is None or str(birim_fiyat).strip() in ('', 'None'):
            row['birim_fiyat'] = 0
        
        for date_field in ['alis_tarihi', 'ihale_tarihi']:
            value = row.get(date_field)
            if value is None or str(value).strip() in ('', 'None'):
                row[date_field] = None
            else:
                date_str = str(value).strip()
                if ' ' in date_str:
                    date_str = date_str.split(' ')[0]
                row[date_field] = date_str
        
        for field in ['toplam_ihale_miktari', 'toplam_adet']:
            value = row.get(field)
            if value is None or str(value).strip() in ('', 'None'):
                row[field] = 0
        
        kalan_miktar = row.get('kalan_miktar')
        if kalan_miktar is None or str(kalan_miktar).strip() in ('', 'None'):
            row['kalan_miktar'] = 0
        
        kalan_adet = row.get('kalan_adet')
        if kalan_adet is None or str(kalan_adet).strip() in ('', 'None'):
            row['kalan_adet'] = 0
        
        return row
    
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        for i, header in enumerate(dataset.headers):
            if header:
                dataset.headers[i] = str(header).strip()
        
        rows_to_delete = []
        for i, row in enumerate(dataset):
            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                rows_to_delete.append(i)
            else:
                kik_no = row[0] if len(row) > 0 else ''
                if not kik_no or str(kik_no).strip() in ('', 'None'):
                    rows_to_delete.append(i)
        
        for i in reversed(rows_to_delete):
            del dataset[i]
        
        return dataset
    
    def after_import_row(self, row, row_result, **kwargs):
        if row_result.instance:
            instance = row_result.instance
            instance.update_kalan()
    
    def get_instance(self, instance_loader, row):
        return None
    
    class Meta:
        model = Ihale
        fields = [
            'sistem_ihale_no',
            'kik_no', 
            'tedarikci',
            'urun_adi', 
            'alis_tarihi', 
            'parti_no', 
            'istif_no', 
            'boy',
            'toplam_ihale_miktari', 
            'kalan_miktar', 
            'toplam_adet', 
            'kalan_adet',
            'birim_fiyat', 
            'toplam_tutar', 
            'durum', 
            'odeme_durumu', 
            'ihale_tarihi', 
            'aciklama'
        ]
        export_order = fields
        skip_unchanged = True
        report_skipped = True
        
        widgets = {
            'alis_tarihi': {'format': '%Y-%m-%d'},
            'ihale_tarihi': {'format': '%Y-%m-%d'},
        }


# ==================== İHALE SEVK RESOURCE ====================
class IhaleSevkResource(resources.ModelResource):
    
    def before_import_row(self, row, row_number=None, **kwargs):
        from .models import Ihale
        
        if not isinstance(row, dict):
            row = dict(row)
        
        ihale_no = row.get('sistem_ihale_no', '')
        if not ihale_no:
            ihale_no = row.get('ihale', '')
        
        if ihale_no and str(ihale_no).strip():
            try:
                ihale = Ihale.objects.get(sistem_ihale_no=str(ihale_no).strip())
                row['ihale'] = ihale.id
            except Ihale.DoesNotExist:
                try:
                    ihale = Ihale.objects.get(id=int(ihale_no))
                    row['ihale'] = ihale.id
                except (Ihale.DoesNotExist, ValueError):
                    row['ihale'] = None
                    row['_ihale_hata'] = f"İhale bulunamadı: {ihale_no}"
        else:
            row['ihale'] = None
            row['_ihale_hata'] = "İhale numarası boş"
        
        sevk_tarihi = row.get('sevk_tarihi', '')
        if sevk_tarihi and str(sevk_tarihi).strip() not in ('', 'None'):
            date_str = str(sevk_tarihi).strip()
            if ' ' in date_str:
                date_str = date_str.split(' ')[0]
            row['sevk_tarihi'] = date_str
        else:
            row['sevk_tarihi'] = None
        
        for field in ['sevk_miktar', 'kalan_miktar']:
            value = row.get(field)
            if value is not None and str(value).strip() not in ('', 'None'):
                try:
                    row[field] = round(float(value), 4)
                except (ValueError, TypeError):
                    row[field] = 0
            else:
                row[field] = 0
        
        for field in ['sevk_adet', 'kalan_adet']:
            value = row.get(field)
            if value is not None and str(value).strip() not in ('', 'None'):
                try:
                    row[field] = int(float(value))
                except (ValueError, TypeError):
                    row[field] = 0
            else:
                row[field] = 0
        
        return row
    
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        for i, header in enumerate(dataset.headers):
            if header:
                dataset.headers[i] = str(header).strip()
        
        rows_to_delete = []
        for i, row in enumerate(dataset):
            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                rows_to_delete.append(i)
            else:
                ihale_no = row[0] if len(row) > 0 else ''
                if not ihale_no or str(ihale_no).strip() in ('', 'None'):
                    rows_to_delete.append(i)
        
        for i in reversed(rows_to_delete):
            del dataset[i]
        
        return dataset
    
    def after_import_row(self, row, row_result, **kwargs):
        if row_result.instance and row_result.instance.ihale:
            row_result.instance.ihale.update_kalan()
    
    def get_instance(self, instance_loader, row):
        from .models import IhaleSevk
        
        ihale_id = row.get('ihale')
        sevk_tarihi = row.get('sevk_tarihi', '')
        sevk_miktar = row.get('sevk_miktar', 0)
        
        if ihale_id and sevk_tarihi:
            try:
                return IhaleSevk.objects.get(
                    ihale_id=ihale_id,
                    sevk_tarihi=sevk_tarihi,
                    sevk_miktar=round(float(sevk_miktar), 4)
                )
            except IhaleSevk.DoesNotExist:
                pass
            except IhaleSevk.MultipleObjectsReturned:
                pass
        
        return None
    
    class Meta:
        model = IhaleSevk
        fields = [
            'ihale',
            'sevk_tarihi',
            'sevk_miktar',
            'sevk_adet',
            'kalan_miktar',
            'kalan_adet'
        ]
        export_order = [
            'ihale',
            'sevk_tarihi',
            'sevk_miktar',
            'sevk_adet',
            'kalan_miktar',
            'kalan_adet'
        ]
        skip_unchanged = True
        report_skipped = True
        
        widgets = {
            'sevk_tarihi': {'format': '%Y-%m-%d'},
        }


# ==================== STOK HAREKET RESOURCE ====================
class StokHareketResource(resources.ModelResource):
    """StokHareket Excel export — ana ekrandaki tüm sütunlar (açıklama hariç)"""
    
    # ===== İLİŞKİLİ ALANLAR =====
    urun_adi = fields.Field(
        column_name='Ürün',
        attribute='urun',
    )
    hareket_tipi_display = fields.Field(
        column_name='Hareket Tipi',
        attribute='hareket_tipi',
    )
    tedarikci = fields.Field(
        column_name='Kaynak / Tedarikçi',
        attribute='ihale',
    )
    parti_no = fields.Field(
        column_name='Parti No',
        attribute='ihale',
    )
    istif_no = fields.Field(
        column_name='İstif No',
        attribute='ihale',
    )
    alis_tarihi = fields.Field(
        column_name='Alış Tarihi',
        attribute='ihale',
    )
    miktar = fields.Field(
        column_name='Miktar (m³)',
        attribute='miktar',
    )
    birim_fiyat = fields.Field(
        column_name='Birim Fiyat',
        attribute='birim_fiyat',
    )
    toplam_tutar = fields.Field(
        column_name='Toplam Tutar',
        attribute='toplam_tutar',
    )
    kalan_miktar = fields.Field(
        column_name='Kalan Miktar (m³)',
        attribute='ihale',
    )
    kalan_adet = fields.Field(
        column_name='Kalan Adet',
        attribute='ihale',
    )
    tarih = fields.Field(
        column_name='Tarih',
        attribute='tarih',
    )

    # ===== DEHYDRATE METODLARI =====
    def dehydrate_urun_adi(self, obj):
        return obj.urun.urun_adi if obj.urun else ''

    def dehydrate_hareket_tipi_display(self, obj):
        return obj.get_hareket_tipi_display()

    def dehydrate_tedarikci(self, obj):
        if obj.ihale and obj.ihale.tedarikci:
            return obj.ihale.tedarikci.unvan
        if obj.uretim:
            return f"Üretim: {obj.uretim.uretim_no}"
        return obj.get_hareket_tipi_display()

    def dehydrate_parti_no(self, obj):
        if obj.ihale:
            return obj.ihale.parti_no or ''
        return ''

    def dehydrate_istif_no(self, obj):
        if obj.ihale:
            return obj.ihale.istif_no or ''
        return ''

    def dehydrate_alis_tarihi(self, obj):
        if obj.ihale and obj.ihale.alis_tarihi:
            return obj.ihale.alis_tarihi.strftime('%d.%m.%Y')
        return ''

    def dehydrate_miktar(self, obj):
        return float(obj.miktar) if obj.miktar else 0

    def dehydrate_birim_fiyat(self, obj):
        return float(obj.birim_fiyat) if obj.birim_fiyat else 0

    def dehydrate_toplam_tutar(self, obj):
        return float(obj.toplam_tutar) if obj.toplam_tutar else 0

    def dehydrate_kalan_miktar(self, obj):
        if obj.ihale:
            return float(obj.ihale.kalan_miktar)
        return ''

    def dehydrate_kalan_adet(self, obj):
        if obj.ihale:
            return obj.ihale.kalan_adet
        return ''

    def dehydrate_tarih(self, obj):
        if obj.tarih:
            return obj.tarih.strftime('%d.%m.%Y %H:%M')
        return ''

    class Meta:
        model = StokHareket
        # ===== SÜTUN SIRASI — ANA EKRANLA AYNI =====
        fields = (
            'urun_adi',              # 1. Ürün
            'hareket_tipi_display',  # 2. Hareket Tipi
            'tedarikci',             # 3. Kaynak / Tedarikçi
            'parti_no',              # 4. Parti No
            'istif_no',              # 5. İstif No
            'alis_tarihi',           # 6. Alış Tarihi
            'miktar',                # 7. Miktar (m³)
            'birim_fiyat',           # 8. Birim Fiyat
            'toplam_tutar',          # 9. Toplam Tutar
            'kalan_miktar',          # 10. Kalan Miktar (m³)
            'kalan_adet',            # 11. Kalan Adet
            'tarih',                 # 12. Tarih
        )
        export_order = fields   # ← Aynı sıra ile dışa aktar
        skip_unchanged = True
        report_skipped = True


# ==================== DEPO RESOURCE ====================
class DepoResource(resources.ModelResource):
    class Meta:
        model = Depo
        fields = ['kod', 'ad', 'adres', 'telefon', 'yetkili', 'aktif_mi']
        export_order = ['kod', 'ad', 'adres', 'telefon', 'yetkili', 'aktif_mi']
        import_id_fields = ['kod']


# ==================== MAKİNE RESOURCE ====================
class MakineResource(resources.ModelResource):
    class Meta:
        model = Makine
        fields = ['kod', 'ad', 'model', 'durum', 'saatlik_kapasite', 'aciklama']
        export_order = ['kod', 'ad', 'model', 'durum', 'saatlik_kapasite', 'aciklama']
        import_id_fields = ['kod']


# ==================== İHALE SEVK INLINE ====================
class IhaleSevkInline(admin.TabularInline):
    model = IhaleSevk
    extra = 0
    can_delete = True
    # ★★★ BU SATIRI EKLE ★★★
    autocomplete_fields = ['tasiyici', 'tasiyici_arac']
    fields = (
        'sevk_tarihi',
        'sevk_miktar',
        'sevk_adet',
        'tasiyici',
        'tasiyici_arac',
        'irsaliye_no',
        'tasima_birim_fiyat',
        'tasima_toplam_tutar',
        'tasima_odeme_durumu',       # ← YENİ
        'tasima_odenen_tutar',       # ← YENİ
        'kalan_miktar',
        'kalan_adet',
    )
    readonly_fields = [
        'kalan_miktar', 'kalan_adet', 'tasima_toplam_tutar',
        'tasima_odeme_durumu', 'tasima_odenen_tutar',
    ]
    ordering = ['-sevk_tarihi']


# ==================== ADMIN KAYITLARI ====================
@admin.register(NACEKodu)
class NACEKoduAdmin(ImportExportModelAdmin):
    resource_class = NACEKoduResource
    list_display = ['kod', 'aciklama', 'sistem_kodu', 'aktif_mi']
    list_filter = ['sistem_kodu', 'aktif_mi']
    search_fields = ['kod', 'aciklama']
    list_editable = ['aktif_mi']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']


@admin.register(Urun)
class UrunAdmin(ImportExportModelAdmin):
    resource_class = UrunResource
    list_display = ['urun_kodu', 'urun_adi', 'nace_kodu', 'urun_tipi', 'mevcut_miktar', 'stokta_mi']
    list_filter = ['nace_kodu', 'urun_tipi', 'stokta_mi']
    search_fields = ['urun_kodu', 'urun_adi', 'nace_kodu__kod', 'nace_kodu__aciklama']
    readonly_fields = ['mevcut_miktar', 'toplam_giren', 'toplam_cikan']
    autocomplete_fields = ['nace_kodu']


@admin.register(Tedarikci)
class TedarikciAdmin(ImportExportModelAdmin):
    resource_class = TedarikciResource
    list_display = ['kod', 'unvan', 'tedarikci_tipi', 'telefon', 'aktif_mi']
    list_filter = ['tedarikci_tipi', 'aktif_mi']
    search_fields = ['kod', 'unvan', 'vergi_no', 'telefon']


# ==================== İHALE ADMIN ====================
@admin.register(Ihale)
class IhaleAdmin(ImportExportModelAdmin):
    resource_class = IhaleResource
    
    list_display = [
        'kik_no',
        'parti_no',
        'istif_no_short',
        'tedarikci',
        'toplam_ihale_miktari',
        'kalan_miktar',
        'toplam_adet',
        'kalan_adet',
        'durum_badge_display',
        'odeme_badge_display',
    ]
    
    list_filter = [
        TedarikciFilter,
        'durum',
        'odeme_durumu',
        ('alis_tarihi', admin.DateFieldListFilter),
        ('ihale_tarihi', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'kik_no',
        'parti_no',
        'istif_no',
        'tedarikci__unvan',
        'tedarikci__kod',
        'urun_adi',
        'boy',
    ]
    
    exclude = ['sistem_ihale_no']
    
    readonly_fields = [
        'toplam_tutar',
        'ihale_tarihi',
        'olusturma_tarihi',
        'guncelleme_tarihi',
        'kalan_miktar',
        'kalan_adet',
        'toplam_partiler_badge',
        'toplam_ihale_miktari_icmal',
        'toplam_kalan_miktar_icmal',
        'toplam_adet_icmal',
        'toplam_kalan_adet_icmal',
        'tum_partiler_listesi'
    ]
    
    inlines = [IhaleSevkInline]
    
    fieldsets = (
        ('İhale Bilgileri', {
            'fields': (
                'kik_no',
                'tedarikci',
                'urun_adi',
                'alis_tarihi',
                'parti_no',
                'istif_no',
                'boy',
                'toplam_ihale_miktari',
                'toplam_adet',
                'birim_fiyat',
                'durum',
                'odeme_durumu',
                'aciklama'
            )
        }),
        ('📊 Aynı KİK Numarasına Ait Tüm Partiler (İCMAL)', {
            'fields': (
                'toplam_partiler_badge',
                'toplam_ihale_miktari_icmal',
                'toplam_kalan_miktar_icmal',
                'toplam_adet_icmal',
                'toplam_kalan_adet_icmal',
                'tum_partiler_listesi'
            ),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Sistem Bilgileri', {
            'fields': (
                'ihale_tarihi',
                'toplam_tutar',
                'olusturan'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def istif_no_short(self, obj):
        return obj.istif_no[:30] + '...' if len(obj.istif_no) > 30 else obj.istif_no
    istif_no_short.short_description = "İstif No"
    
    def toplam_partiler_badge(self, obj):
        if not obj.kik_no:
            return "1"
        count = Ihale.objects.filter(kik_no=obj.kik_no).count()
        return count
    toplam_partiler_badge.short_description = "Toplam Parti"
    
    def durum_badge_display(self, obj):
        colors = {
            'devam_ediyor': 'warning',
            'tamamlandi': 'success',
            'iptal': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.durum, 'secondary'),
            obj.get_durum_display()
        )
    durum_badge_display.short_description = "Durum"
    
    def odeme_badge_display(self, obj):
        colors = {
            'odenmedi': 'danger',
            'kismi_odendi': 'warning',
            'tamamen_odendi': 'success'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.odeme_durumu, 'secondary'),
            obj.get_odeme_durumu_display()
        )
    odeme_badge_display.short_description = "Ödeme"
    
    def toplam_ihale_miktari_icmal(self, obj):
        if not obj.kik_no:
            return f"{obj.toplam_ihale_miktari:.4f} m³"
        toplam = Ihale.objects.filter(kik_no=obj.kik_no).aggregate(
            toplam=models.Sum('toplam_ihale_miktari')
        )['toplam'] or 0
        return f"{toplam:.4f} m³"
    toplam_ihale_miktari_icmal.short_description = "Toplam Miktar"

    def toplam_kalan_miktar_icmal(self, obj):
        if not obj.kik_no:
            return f"{obj.kalan_miktar:.4f} m³"
        toplam = Ihale.objects.filter(kik_no=obj.kik_no).aggregate(
            toplam=models.Sum('kalan_miktar')
        )['toplam'] or 0
        return f"{toplam:.4f} m³"
    toplam_kalan_miktar_icmal.short_description = "Toplam Kalan"

    def toplam_adet_icmal(self, obj):
        if not obj.kik_no:
            return f"{obj.toplam_adet} Adet"
        toplam = Ihale.objects.filter(kik_no=obj.kik_no).aggregate(
            toplam=models.Sum('toplam_adet')
        )['toplam'] or 0
        return f"{toplam} Adet"
    toplam_adet_icmal.short_description = "Toplam Adet"

    def toplam_kalan_adet_icmal(self, obj):
        if not obj.kik_no:
            return f"{obj.kalan_adet} Adet"
        toplam = Ihale.objects.filter(kik_no=obj.kik_no).aggregate(
            toplam=models.Sum('kalan_adet')
        )['toplam'] or 0
        return f"{toplam} Adet"
    toplam_kalan_adet_icmal.short_description = "Toplam Kalan Adet"

    def tum_partiler_listesi(self, obj):
        if not obj.kik_no:
            return format_html(
                '<div class="alert alert-warning">⚠️ KİK numarası tanımlanmamış.</div>'
            )
        
        partiler = Ihale.objects.filter(kik_no=obj.kik_no)
        
        html = '''
        <div style="background: #ffffff; border-radius: 8px; padding: 15px; border: 1px solid #dee2e6; overflow-x: auto;">
            <table style="width:100%; border-collapse:collapse; font-size:13px; min-width:850px;">
                <thead>
                    <tr style="background: #f8f9fa;">
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Parti No</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">İstif No</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Miktar (m³)</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Kalan (m³)</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Adet</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Kalan Adet</th>
                        <th style="padding:8px 10px; text-align:center; border-bottom:2px solid #dee2e6;">Durum</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for p in partiler:
            colors = {
                'devam_ediyor': ('#ffc107', '#000'),
                'tamamlandi': ('#198754', '#fff'),
                'iptal': ('#dc3545', '#fff')
            }
            durum_bg, durum_text = colors.get(p.durum, ('#6c757d', '#fff'))
            satir_renk = '#e7f1ff' if p.id == obj.id else 'white'
            is_current = '⭐ ' if p.id == obj.id else ''
            
            html += f'''
                <tr style="background:{satir_renk}; border-bottom:1px solid #f1f3f5;">
                    <td style="padding:8px 10px; text-align:center; font-weight:600;">{is_current}{p.parti_no}</td>
                    <td style="padding:8px 10px; text-align:center;">{p.istif_no or '-'}</td>
                    <td style="padding:8px 10px; text-align:center;">{p.toplam_ihale_miktari:.4f}</td>
                    <td style="padding:8px 10px; text-align:center; font-weight:bold; color:{'#198754' if p.kalan_miktar > 0 else '#dc3545'}">{p.kalan_miktar:.4f}</td>
                    <td style="padding:8px 10px; text-align:center;">{p.toplam_adet}</td>
                    <td style="padding:8px 10px; text-align:center; font-weight:bold; color:{'#198754' if p.kalan_adet > 0 else '#dc3545'}">{p.kalan_adet}</td>
                    <td style="padding:8px 10px; text-align:center;"><span style="background:{durum_bg}; color:{durum_text}; padding:2px 10px; border-radius:12px; font-size:11px;">{p.get_durum_display()}</span></td>
                </tr>
            '''
        
        toplam_miktar = partiler.aggregate(toplam=models.Sum('toplam_ihale_miktari'))['toplam'] or 0
        toplam_kalan = partiler.aggregate(toplam=models.Sum('kalan_miktar'))['toplam'] or 0
        toplam_adet = partiler.aggregate(toplam=models.Sum('toplam_adet'))['toplam'] or 0
        toplam_kalan_adet = partiler.aggregate(toplam=models.Sum('kalan_adet'))['toplam'] or 0
        
        html += f'''
            <tr style="background:#e9ecef; font-weight:bold; border-top:3px solid #0d6efd;">
                <td style="padding:10px; text-align:center;"><span style="background:#0d6efd; color:white; padding:2px 12px; border-radius:12px; font-size:11px;">TOPLAM</span></td>
                <td style="padding:10px; text-align:center;">-</td>
                <td style="padding:10px; text-align:center; color:#0d6efd; font-size:15px;">{toplam_miktar:.4f} m³</td>
                <td style="padding:10px; text-align:center; color:#198754; font-size:15px;">{toplam_kalan:.4f} m³</td>
                <td style="padding:10px; text-align:center; color:#0d6efd; font-size:15px;">{toplam_adet}</td>
                <td style="padding:10px; text-align:center; color:#198754; font-size:15px;">{toplam_kalan_adet}</td>
                <td style="padding:10px; text-align:center;">-</td>
            </tr>
        '''
        
        html += '''
                </tbody>
            </table>
            <div style="margin-top:6px; font-size:11px; color:#adb5bd; text-align:right;">⭐ Mevcut parti</div>
        </div>
        '''
        
        return format_html(html)
    tum_partiler_listesi.short_description = "Aynı KİK Numarasına Ait Tüm Partiler"
    
    def changelist_view(self, request, extra_context=None):
        # Django'nun standart işleyişini bozmadan çalıştır
        response = super().changelist_view(request, extra_context=extra_context)
        
        # ===== REDIRECT KONTROLÜ =====
        # Eğer response bir redirect ise (context_data yoksa), dokunmadan geri dön
        if not hasattr(response, 'context_data'):
            return response
        
        # Django'nun filtrelenmiş queryset'ini al
        try:
            cl = response.context_data['cl']
            queryset = cl.queryset
        except (AttributeError, KeyError):
            queryset = self.get_queryset(request)
        
        # Toplamları hesapla (arama + filtreler dahil)
        total_miktar = queryset.aggregate(total=models.Sum('toplam_ihale_miktari'))['total'] or 0
        total_kalan = queryset.aggregate(total=models.Sum('kalan_miktar'))['total'] or 0
        total_adet = queryset.aggregate(total=models.Sum('toplam_adet'))['total'] or 0
        total_kalan_adet = queryset.aggregate(total=models.Sum('kalan_adet'))['total'] or 0
        total_kayit = queryset.count()
        
        toplam_html = ''
        if queryset.exists():
            toplam_html = f'''
            <div style="margin-top: 15px; background: #f8f9fa; border-radius: 8px; border: 2px solid #0d6efd; padding: 10px 15px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #0d6efd; color: white; font-weight: bold; font-size: 14px; text-align: center;">
                        <td style="padding: 12px 15px; border-radius: 6px 0 0 6px; width: 13%;">
                            <i class="fas fa-calculator"></i> TOPLAM
                        </td>
                        <td style="padding: 12px 15px; width: 14%; background: #0a58ca;">
                            {total_miktar:.4f} m³
                        </td>
                        <td style="padding: 12px 15px; width: 14%; background: #0a58ca; color: #ffc107;">
                            {total_kalan:.4f} m³
                        </td>
                        <td style="padding: 12px 15px; width: 14%; background: #0a58ca;">
                            {total_adet}
                        </td>
                        <td style="padding: 12px 15px; width: 14%; background: #0a58ca; color: #ffc107;">
                            {total_kalan_adet}
                        </td>
                        <td style="padding: 12px 15px; border-radius: 0 6px 6px 0; width: 31%; background: #0a58ca; text-align: left; padding-left: 20px;">
                            <span style="background: rgba(255,255,255,0.2); padding: 4px 14px; border-radius: 20px;">
                                {total_kayit} Kayıt
                            </span>
                        </td>
                    </tr>
                </table>
                <div style="font-size: 11px; color: #6c757d; text-align: right; margin-top: 4px;">
                    Filtrelenmiş verilere göre hesaplanmıştır.
                </div>
            </div>
            '''
        
        response.context_data['toplam_html'] = toplam_html
        return response


# ==================== TAŞIYICI ÖDEME INLINE ====================
class TasiyiciOdemeInline(admin.TabularInline):
    model = TasiyiciOdeme
    extra = 1
    fields = (
        'odeme_tarihi', 'odeme_tutari', 'odeme_tipi', 'aciklama'
    )
    ordering = ['-odeme_tarihi']

@admin.register(IhaleSevk)
class IhaleSevkAdmin(ImportExportModelAdmin):
    resource_class = IhaleSevkResource

    # ★★★ BU SATIRI EKLE ★★★
    autocomplete_fields = ['ihale', 'tasiyici', 'tasiyici_arac']

    list_display = [
        'ihale', 'sevk_tarihi', 'tasiyici', 'tasiyici_arac',
        'sevk_miktar', 'sevk_adet', 'kalan_miktar', 'kalan_adet',
        'tasima_birim_fiyat', 'tasima_toplam_tutar',
        'tasima_odeme_durumu_badge',
    ]
    
    search_fields = [
        'ihale__sistem_ihale_no',
        'ihale__parti_no',
        'tasiyici__ad',
        'irsaliye_no',
        'fatura_no',
    ]
    readonly_fields = [
    'kalan_miktar', 'kalan_adet', 'tasima_toplam_tutar',
    'tasima_odeme_durumu', 'tasima_odenen_tutar',
]
    inlines = [TasiyiciOdemeInline]
    
    fieldsets = (
        ('Sevk Bilgileri', {
            'fields': (
                'ihale',
                'sevk_tarihi',
                'sevk_miktar',
                'sevk_adet',
                'kalan_miktar',
                'kalan_adet',
            )
        }),
        ('Taşıyıcı Bilgileri', {
            'fields': (
                'tasiyici',
                'tasiyici_arac',
                'irsaliye_no',
                'nereden',
                'nereye',
            )
        }),
        ('💰 TAŞIMA ÜCRETİ', {
            'fields': (
                'tasima_birim_fiyat',
                'tasima_toplam_tutar',
            ),
        }),
        ('💳 FATURA BİLGİLERİ', {
            'fields': (
                'fatura_no',
                'fatura_tarihi',
            ),
            'classes': ('collapse',)
        }),
        ('✅ TAŞIMA ÖDEME DURUMU (Otomatik)', {
            'fields': (
                'tasima_odeme_durumu',
                'tasima_odenen_tutar',
            ),
        }),
    )
    
    def tasima_odeme_durumu_badge(self, obj):
        colors = {
            'odenmedi': 'danger',
            'kismi_odendi': 'warning',
            'tamamen_odendi': 'success',
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.tasima_odeme_durumu, 'secondary'),
            obj.get_tasima_odeme_durumu_display()
        )
    tasima_odeme_durumu_badge.short_description = "Taşıma Ödeme"

    def delete_queryset(self, request, queryset):
        """Toplu silmede her bir objeyi tek tek sil (delete() metodu çalışsın)"""
        for obj in queryset:
            obj.delete()


# ==================== STOK HAREKET ADMIN ====================
@admin.register(StokHareket)
class StokHareketAdmin(ImportExportModelAdmin):
    resource_class = StokHareketResource
    
    list_display = [
        'urun',
        'alis_tarihi_display',
        'hareket_tipi',
        'tedarikci_display',
        'parti_no_display',
        'istif_no_display',
        'miktar',
        'birim_fiyat',
        'toplam_tutar',
        'kalan_miktar_display',
        'kalan_adet_display',
        'tarih'
    ]
    
    # ===== FİLTRELER (SIRALAMA ÖNEMLİ!) =====
    list_filter = [
        'hareket_tipi',
        StokHareketTedarikciFilter,
        ('tarih', admin.DateFieldListFilter),
    ]
    
    search_fields = (
        'urun__urun_adi',
        'ihale__tedarikci__unvan',
        'ihale__parti_no',
        'ihale__istif_no',
        'uretim__uretim_no',
    )
    
    readonly_fields = ['toplam_tutar', 'tarih']
    
    fieldsets = (
        ('Hareket Bilgileri', {
            'fields': (
                'urun',
                'hareket_tipi',
                'miktar',
                'birim_fiyat',
                'aciklama'
            )
        }),
        ('İlişkili Kayıtlar', {
            'fields': (
                'ihale',
                'ihale_sevk',
                'uretim',
            ),
            'classes': ('collapse',)
        }),
        ('Sistem Bilgileri', {
            'fields': (
                'toplam_tutar',
                'tarih',
                'kullanici'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def tedarikci_display(self, obj):
        if obj.ihale and obj.ihale.tedarikci:
            return obj.ihale.tedarikci.unvan
        if obj.uretim:
            return f"🏭 Üretim: {obj.uretim.uretim_no}"
        if obj.hareket_tipi == 'siparis_cikis':
            return "📤 Sipariş Çıkış"
        elif obj.hareket_tipi == 'fire':
            return "🔥 Fire"
        elif obj.hareket_tipi == 'iade':
            return "↩️ İade"
        elif obj.hareket_tipi == 'mamul_giris':
            return "📦 Mamul Giriş"
        elif obj.hareket_tipi == 'mamul_cikis':
            return "📦 Mamul Çıkış"
        elif obj.hareket_tipi == 'hammadde_cikis':
            return "🌲 Hammadde Çıkış"
        return '-'
    tedarikci_display.short_description = "Kaynak / Tedarikçi"

    def alis_tarihi_display(self, obj):
        """İhale üzerinden alış tarihini göster"""
        if obj.ihale and obj.ihale.alis_tarihi:
            return obj.ihale.alis_tarihi.strftime('%d.%m.%Y')
        return '-'
    alis_tarihi_display.short_description = "Alış Tarihi"
    alis_tarihi_display.admin_order_field = 'ihale__alis_tarihi'
    
    def parti_no_display(self, obj):
        if obj.ihale:
            return obj.ihale.parti_no or '-'
        return '-'
    parti_no_display.short_description = "Parti No"
    
    def istif_no_display(self, obj):
        if obj.ihale:
            return obj.ihale.istif_no or '-'
        return '-'
    istif_no_display.short_description = "İstif No"
    
    def kalan_miktar_display(self, obj):
        if obj.ihale:
            return f"{obj.ihale.kalan_miktar:.4f}"
        return '-'
    kalan_miktar_display.short_description = "Kalan Miktar (m³)"
    
    def kalan_adet_display(self, obj):
        if obj.ihale:
            return obj.ihale.kalan_adet
        return '-'
    kalan_adet_display.short_description = "Kalan Adet"


@admin.register(Depo)
class DepoAdmin(ImportExportModelAdmin):
    resource_class = DepoResource
    list_display = ['kod', 'ad', 'aktif_mi']
    search_fields = ['kod', 'ad']


@admin.register(Makine)
class MakineAdmin(ImportExportModelAdmin):
    resource_class = MakineResource
    list_display = ['kod', 'ad', 'durum', 'saatlik_kapasite']
    list_filter = ['durum']
    search_fields = ['kod', 'ad']


@admin.register(TedarikciTipi)
class TedarikciTipiAdmin(admin.ModelAdmin):
    list_display = ['ad', 'sistem_tipi', 'aktif_mi']
    list_filter = ['sistem_tipi', 'aktif_mi']
    search_fields = ['ad']


@admin.register(Raf)
class RafAdmin(admin.ModelAdmin):
    list_display = ['depo', 'kod', 'kapasite']
    list_filter = ['depo']
    search_fields = ['kod']


@admin.register(StokBarkod)
class StokBarkodAdmin(admin.ModelAdmin):
    list_display = ['barkod', 'urun', 'depo', 'raf', 'miktar', 'lot_no']
    list_filter = ['depo']
    search_fields = ['barkod', 'urun__urun_adi', 'lot_no']


@admin.register(UretimAsama)
class UretimAsamaAdmin(admin.ModelAdmin):
    list_display = ['recete', 'asama_tipi', 'siralama', 'makine']
    list_filter = ['asama_tipi']
    search_fields = ['recete__recete_adi']


@admin.register(UretimEmri)
class UretimEmriAdmin(admin.ModelAdmin):
    list_display = ['emir_no', 'recete', 'hedef_miktar', 'durum']
    list_filter = ['durum']
    search_fields = ['emir_no', 'recete__recete_adi']


@admin.register(UretimAsamaTakip)
class UretimAsamaTakipAdmin(admin.ModelAdmin):
    list_display = ['emir', 'asama', 'durum', 'baslangic_tarihi']
    list_filter = ['durum']
    search_fields = ['emir__emir_no']


@admin.register(Fire)
class FireAdmin(admin.ModelAdmin):
    list_display = ['uretim', 'urun', 'fire_miktar', 'fire_tipi', 'tarih']
    list_filter = [
        'fire_tipi',
        ('tarih', admin.DateFieldListFilter),
    ]
    search_fields = ['uretim__uretim_no', 'urun__urun_adi']


# ==================== ÜRETİM REÇETESİ ADMIN ====================
class UretimReceteDetayInline(admin.TabularInline):
    model = UretimReceteDetay
    extra = 3


@admin.register(UretimRecete)
class UretimReceteAdmin(admin.ModelAdmin):
    list_display = ['recete_kodu', 'recete_adi', 'hammadde', 'aktif_mi']
    list_filter = ['aktif_mi']
    search_fields = ['recete_kodu', 'recete_adi', 'hammadde__urun_adi']
    inlines = [UretimReceteDetayInline]


@admin.register(Uretim)
class UretimAdmin(admin.ModelAdmin):
    list_display = ['uretim_no', 'recete', 'hammadde', 'kullanilan_miktar', 'durum', 'baslangic_tarihi']
    list_filter = [
        'durum',
        ('baslangic_tarihi', admin.DateFieldListFilter),
    ]
    search_fields = ['uretim_no', 'recete__recete_adi']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']


# ==================== TAŞIYICI ADMIN ====================
class TasiyiciAracInline(admin.TabularInline):
    model = TasiyiciArac
    extra = 1
    fields = (
        'plaka', 'arac_tipi', 'marka', 'model',
        'kapasite_m3', 'sofor_adi', 'sofor_telefon', 'aktif_mi'
    )
    ordering = ['plaka']


@admin.register(Tasiyici)
class TasiyiciAdmin(admin.ModelAdmin):
    list_display = ['kod', 'ad', 'tipi', 'yetkili', 'telefon', 'aktif_mi']
    list_filter = ['tipi', 'aktif_mi']
    search_fields = ['kod', 'ad', 'telefon', 'vergi_no']
    readonly_fields = ['kod', 'olusturma_tarihi', 'guncelleme_tarihi']
    inlines = [TasiyiciAracInline]
    
    fieldsets = (
        ('Kimlik Bilgileri', {
            'fields': ('kod', 'ad', 'tipi', 'yetkili')
        }),
        ('İletişim Bilgileri', {
            'fields': ('telefon', 'email', 'adres')
        }),
        ('Vergi & Banka', {
            'fields': ('vergi_dairesi', 'vergi_no', 'iban'),
            'classes': ('collapse',)
        }),
        ('Diğer', {
            'fields': ('aktif_mi', 'aciklama', 'olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )


@admin.register(TasiyiciArac)
class TasiyiciAracAdmin(admin.ModelAdmin):
    list_display = ['plaka', 'tasiyici', 'arac_tipi', 'marka', 'kapasite_m3', 'sofor_adi', 'aktif_mi']
    list_filter = ['tasiyici', 'aktif_mi']
    search_fields = ['plaka', 'tasiyici__ad', 'sofor_adi']



# ==================== TAŞIYICI ÖDEME ADMIN ====================
@admin.register(TasiyiciOdeme)
class TasiyiciOdemeAdmin(admin.ModelAdmin):
    list_display = [
        'odeme_tarihi', 'tasiyici_ad', 'sevk',
        'odeme_tutari', 'odeme_tipi', 'aciklama_kisa'
    ]
    list_filter = ['odeme_tipi', 'odeme_tarihi', 'sevk__tasiyici']
    search_fields = ['sevk__tasiyici__ad', 'sevk__ihale__sistem_ihale_no', 'aciklama']
    date_hierarchy = 'odeme_tarihi'
    
    def tasiyici_ad(self, obj):
        return obj.sevk.tasiyici.ad if obj.sevk and obj.sevk.tasiyici else '-'
    tasiyici_ad.short_description = "Taşıyıcı"
    
    def aciklama_kisa(self, obj):
        return (obj.aciklama[:50] + '...') if obj.aciklama and len(obj.aciklama) > 50 else (obj.aciklama or '-')
    aciklama_kisa.short_description = "Açıklama"

# ==================== STOK DEVİR ADMIN ====================
@admin.register(StokDevir)
class StokDevirAdmin(admin.ModelAdmin):
    list_display = ['yil', 'ay_goster', 'devir_miktar', 'aciklama_kisa', 'olusturma_tarihi']
    list_filter = ['yil', 'ay']
    search_fields = ['aciklama']
    ordering = ['-yil', '-ay']
    
    def ay_goster(self, obj):
        ay_adi = dict(StokDevir.AY_CHOICES).get(obj.ay, str(obj.ay))
        return f"{ay_adi}"
    ay_goster.short_description = "Ay"
    
    def aciklama_kisa(self, obj):
        return (obj.aciklama[:50] + '...') if obj.aciklama and len(obj.aciklama) > 50 else (obj.aciklama or '-')
    aciklama_kisa.short_description = "Açıklama"