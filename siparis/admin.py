# siparis/admin.py
from django.contrib import admin
from django.db import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Musteri, Siparis, Satis, SatisDetay, SatisIade


# ==================== MÜŞTERİ RESOURCE ====================
class MusteriResource(resources.ModelResource):
    class Meta:
        model = Musteri
        fields = ['musteri_kodu', 'unvan', 'vergi_dairesi', 'vergi_no', 'telefon', 'adres', 'email', 'yetkili']
        export_order = ['musteri_kodu', 'unvan', 'vergi_dairesi', 'vergi_no', 'telefon', 'adres', 'email', 'yetkili']
        import_id_fields = ['musteri_kodu']
        skip_unchanged = True
        report_skipped = True


# ==================== SİPARİŞ RESOURCE ====================
class SiparisResource(resources.ModelResource):
    class Meta:
        model = Siparis
        fields = [
            'siparis_no', 'musteri', 'urun', 'miktar', 
            'birim_fiyat', 'toplam_tutar', 'durum', 
            'siparis_tarihi', 'teslim_tarihi', 'aciklama'
        ]
        export_order = [
            'siparis_no', 'musteri', 'urun', 'miktar', 
            'birim_fiyat', 'toplam_tutar', 'durum', 
            'siparis_tarihi', 'teslim_tarihi', 'aciklama'
        ]
        import_id_fields = ['siparis_no']
        skip_unchanged = True
        report_skipped = True


# ==================== SATIŞ RESOURCE ====================
class SatisResource(resources.ModelResource):
    class Meta:
        model = Satis
        fields = [
            'satis_no', 'musteri', 'urun', 'miktar', 'birim_fiyat',
            'toplam_tutar', 'durum', 'odeme_durumu', 'siparis_tarihi',
            'teslim_tarihi', 'irsaliye_no', 'fatura_no', 'aciklama'
        ]
        export_order = [
            'satis_no', 'musteri', 'urun', 'miktar', 'birim_fiyat',
            'toplam_tutar', 'durum', 'odeme_durumu', 'siparis_tarihi',
            'teslim_tarihi', 'irsaliye_no', 'fatura_no', 'aciklama'
        ]
        import_id_fields = ['satis_no']
        skip_unchanged = True
        report_skipped = True


# ==================== SATIŞ İADE RESOURCE ====================
class SatisIadeResource(resources.ModelResource):
    class Meta:
        model = SatisIade
        fields = ['iade_no', 'satis', 'urun', 'miktar', 'sebep', 'onaylandi_mi', 'aciklama']
        export_order = ['iade_no', 'satis', 'urun', 'miktar', 'sebep', 'onaylandi_mi', 'aciklama']
        import_id_fields = ['iade_no']


# ==================== ADMIN KAYITLARI ====================

# ----- MÜŞTERİ -----
@admin.register(Musteri)
class MusteriAdmin(ImportExportModelAdmin):
    resource_class = MusteriResource
    list_display = ['musteri_kodu', 'unvan', 'vergi_no', 'telefon']
    search_fields = ['musteri_kodu', 'unvan', 'vergi_no']
    readonly_fields = ['musteri_kodu']


# ----- SİPARİŞ -----
@admin.register(Siparis)
class SiparisAdmin(ImportExportModelAdmin):
    resource_class = SiparisResource
    list_display = ['siparis_no', 'musteri', 'urun', 'miktar', 'toplam_tutar', 'durum', 'siparis_tarihi']
    list_filter = ['durum', 'siparis_tarihi', 'musteri']
    search_fields = ['siparis_no', 'musteri__unvan']
    readonly_fields = ['toplam_tutar', 'siparis_tarihi', 'siparis_no']
    list_editable = ['durum']


# ----- SATIŞ DETAY INLINE -----
class SatisDetayInline(admin.TabularInline):
    """Satış detaylarını ana sayfada göster"""
    model = SatisDetay
    extra = 1
    fields = ['urun', 'miktar', 'birim_fiyat', 'toplam_tutar']
    readonly_fields = ['toplam_tutar']


# ----- SATIŞ -----
@admin.register(Satis)
class SatisAdmin(ImportExportModelAdmin):
    resource_class = SatisResource
    list_display = [
        'satis_no', 'musteri', 'urun', 'miktar', 'toplam_tutar',
        'durum', 'odeme_durumu', 'siparis_tarihi'
    ]
    list_filter = ['durum', 'odeme_durumu', 'siparis_tarihi']
    search_fields = ['satis_no', 'musteri__unvan', 'urun__urun_adi']
    readonly_fields = ['satis_no', 'toplam_tutar', 'siparis_tarihi', 'olusturma_tarihi', 'guncelleme_tarihi']
    inlines = [SatisDetayInline]
    list_editable = ['durum', 'odeme_durumu']
    
    fieldsets = (
        ('Satış Bilgileri', {
            'fields': ('satis_no', 'musteri', 'urun', 'miktar', 'birim_fiyat', 'durum', 'odeme_durumu')
        }),
        ('Teslimat Bilgileri', {
            'fields': ('teslim_tarihi', 'irsaliye_no', 'fatura_no')
        }),
        ('Diğer Bilgiler', {
            'fields': ('aciklama', 'siparis_tarihi', 'olusturan'),
            'classes': ('collapse',)
        }),
    )


# ----- SATIŞ İADE -----
@admin.register(SatisIade)
class SatisIadeAdmin(ImportExportModelAdmin):
    resource_class = SatisIadeResource
    list_display = ['iade_no', 'satis', 'urun', 'miktar', 'onaylandi_mi', 'iade_tarihi']
    list_filter = ['onaylandi_mi', 'iade_tarihi']
    search_fields = ['iade_no', 'satis__satis_no', 'urun__urun_adi']
    readonly_fields = ['iade_no', 'olusturma_tarihi']
    list_editable = ['onaylandi_mi']
    
    fieldsets = (
        ('İade Bilgileri', {
            'fields': ('iade_no', 'satis', 'urun', 'miktar', 'sebep')
        }),
        ('Onay Bilgileri', {
            'fields': ('onaylandi_mi', 'onaylayan')
        }),
        ('Diğer Bilgiler', {
            'fields': ('aciklama', 'olusturma_tarihi'),
            'classes': ('collapse',)
        }),
    )