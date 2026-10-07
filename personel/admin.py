# personel/admin.py
from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Personel, Departman, Vardiya, Izin, MesaiTakip


# ==================== RESOURCE SINIFLARI ====================
class PersonelResource(resources.ModelResource):
    class Meta:
        model = Personel
        fields = [
            'sicil_no', 'ad', 'soyad', 'tc_kimlik', 'dogum_tarihi',
            'telefon', 'cep_telefonu', 'email', 'adres',
            'departman', 'unvan', 'ise_giris_tarihi', 'calisma_durumu',
            'maas', 'ek_odeme', 'egitim_durumu', 'medeni_durum'
        ]
        export_order = [
            'sicil_no', 'ad', 'soyad', 'tc_kimlik', 'dogum_tarihi',
            'telefon', 'cep_telefonu', 'email', 'adres',
            'departman', 'unvan', 'ise_giris_tarihi', 'calisma_durumu',
            'maas', 'ek_odeme', 'egitim_durumu', 'medeni_durum'
        ]
        import_id_fields = ['sicil_no']
        skip_unchanged = True
        report_skipped = True


# ==================== ADMIN SINIFLARI ====================
@admin.register(Departman)
class DepartmanAdmin(admin.ModelAdmin):
    list_display = ['kod', 'ad', 'aktif_mi']
    list_filter = ['aktif_mi']
    search_fields = ['kod', 'ad']
    list_editable = ['aktif_mi']


class IzinInline(admin.TabularInline):
    model = Izin
    extra = 0
    fields = ['izin_tipi', 'baslangic_tarihi', 'bitis_tarihi', 'gun_sayisi', 'durum']
    readonly_fields = ['gun_sayisi']


class VardiyaInline(admin.TabularInline):
    model = Vardiya
    extra = 0
    fields = ['vardiya_tipi', 'tarih', 'baslangic_saati', 'bitis_saati']


@admin.register(Personel)
class PersonelAdmin(ImportExportModelAdmin):
    resource_class = PersonelResource
    list_display = [
        'sicil_no', 'tam_adi', 'departman', 'unvan', 'calisma_durumu', 
        'maas', 'telefon', 'yil_donumu'
    ]
    list_filter = ['calisma_durumu', 'departman', 'cinsiyet', 'medeni_durum', 'egitim_durumu']
    search_fields = ['sicil_no', 'ad', 'soyad', 'tc_kimlik', 'telefon']
    list_editable = ['maas', 'unvan', 'calisma_durumu']
    readonly_fields = ['yas', 'calisma_suresi', 'olusturma_tarihi', 'guncelleme_tarihi']
    inlines = [IzinInline, VardiyaInline]
    
    fieldsets = (
        ('Kimlik Bilgileri', {
            'fields': (
                'user', 'sicil_no', 'ad', 'soyad', 'tc_kimlik',
                'dogum_tarihi', 'dogum_yeri', 'cinsiyet', 'kan_grubu',
                'medeni_durum', 'cocuk_sayisi'
            )
        }),
        ('İletişim Bilgileri', {
            'fields': ('telefon', 'cep_telefonu', 'email', 'adres', 
                      'acil_durum_kisi', 'acil_durum_telefon')
        }),
        ('İş Bilgileri', {
            'fields': ('departman', 'unvan', 'ise_giris_tarihi', 
                      'isten_cikis_tarihi', 'calisma_durumu')
        }),
        ('Maaş Bilgileri', {
            'fields': ('maas', 'maas_birimi', 'ek_odeme', 'prim_orani')
        }),
        ('Eğitim Bilgileri', {
            'fields': ('egitim_durumu', 'okul', 'bolum', 'mezuniyet_yili')
        }),
        ('Diğer Bilgiler', {
            'fields': ('ehliyet', 'bildigi_diller', 'sertifikalar', 'notlar'),
            'classes': ('collapse',)
        }),
        ('Sistem Bilgileri', {
            'fields': ('yas', 'calisma_suresi', 'olusturan', 'olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )
    
    def tam_adi(self, obj):
        return format_html(
            '<strong>{}</strong>', obj.tam_adi()
        )
    tam_adi.short_description = "Ad Soyad"
    
    def yil_donumu(self, obj):
        """Yıl dönümü (işe girişin kaçıncı yılı)"""
        return obj.calisma_suresi()
    yil_donumu.short_description = "Çalışma Süresi"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt
            obj.olusturan = request.user
        super().save_model(request, obj, form, change)


@admin.register(Izin)
class IzinAdmin(admin.ModelAdmin):
    list_display = ['personel', 'izin_tipi', 'baslangic_tarihi', 'bitis_tarihi', 'gun_sayisi', 'durum']
    list_filter = ['izin_tipi', 'durum', 'baslangic_tarihi']
    search_fields = ['personel__ad', 'personel__soyad', 'aciklama']
    list_editable = ['durum']
    readonly_fields = ['gun_sayisi', 'olusturma_tarihi']
    
    fieldsets = (
        ('İzin Bilgileri', {
            'fields': ('personel', 'izin_tipi', 'baslangic_tarihi', 'bitis_tarihi', 'gun_sayisi', 'aciklama')
        }),
        ('Onay Bilgileri', {
            'fields': ('durum', 'onaylayan', 'onay_tarihi')
        }),
        ('Sistem Bilgileri', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'onaylandi' in form.changed_data or obj.durum == 'onaylandi':
            if not obj.onaylayan:
                obj.onaylayan = request.user
                obj.onay_tarihi = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(Vardiya)
class VardiyaAdmin(admin.ModelAdmin):
    list_display = ['personel', 'vardiya_tipi', 'tarih', 'baslangic_saati', 'bitis_saati']
    list_filter = ['vardiya_tipi', 'tarih']
    search_fields = ['personel__ad', 'personel__soyad']
    list_editable = ['baslangic_saati', 'bitis_saati']


@admin.register(MesaiTakip)
class MesaiTakipAdmin(admin.ModelAdmin):
    list_display = ['personel', 'tarih', 'gelis_saati', 'cikis_saati', 'toplam_calisma']
    list_filter = ['tarih']
    search_fields = ['personel__ad', 'personel__soyad']
    list_editable = ['gelis_saati', 'cikis_saati']
    readonly_fields = ['toplam_calisma', 'fazla_mesai']