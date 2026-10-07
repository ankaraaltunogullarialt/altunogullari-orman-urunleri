# finans/admin.py
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CariHesap, CariHareket, Banka, BankaHareket


# ==================== CARİ HESAP RESOURCE ====================
class CariHesapResource(resources.ModelResource):
    class Meta:
        model = CariHesap
        fields = ['musteri', 'tedarikci', 'hesap_tipi', 'bakiye', 'limit', 'aciklama']
        export_order = ['musteri', 'tedarikci', 'hesap_tipi', 'bakiye', 'limit', 'aciklama']


# ==================== CARİ HAREKET RESOURCE ====================
class CariHareketResource(resources.ModelResource):
    class Meta:
        model = CariHareket
        fields = ['cari', 'hareket_tipi', 'kaynak_tipi', 'tutar', 'vade_tarihi', 'aciklama', 'tarih']
        export_order = ['cari', 'hareket_tipi', 'kaynak_tipi', 'tutar', 'vade_tarihi', 'aciklama', 'tarih']


# ==================== BANKA RESOURCE ====================
class BankaResource(resources.ModelResource):
    class Meta:
        model = Banka
        fields = ['ad', 'sube', 'hesap_no', 'iban', 'hesap_tipi', 'bakiye', 'para_birimi', 'aktif_mi']
        export_order = ['ad', 'sube', 'hesap_no', 'iban', 'hesap_tipi', 'bakiye', 'para_birimi', 'aktif_mi']


# ==================== ADMIN KAYITLARI ====================
@admin.register(CariHesap)
class CariHesapAdmin(ImportExportModelAdmin):
    resource_class = CariHesapResource
    list_display = ['__str__', 'hesap_tipi', 'bakiye', 'limit']
    list_filter = ['hesap_tipi']
    search_fields = ['musteri__unvan', 'tedarikci__unvan']
    readonly_fields = ['bakiye', 'borc', 'alacak']


@admin.register(CariHareket)
class CariHareketAdmin(ImportExportModelAdmin):
    resource_class = CariHareketResource
    list_display = ['cari', 'hareket_tipi', 'tutar', 'tarih']
    list_filter = ['hareket_tipi', 'kaynak_tipi', 'tarih']
    search_fields = ['cari__musteri__unvan', 'cari__tedarikci__unvan']
    readonly_fields = ['tarih']


@admin.register(Banka)
class BankaAdmin(ImportExportModelAdmin):
    resource_class = BankaResource
    list_display = ['ad', 'hesap_no', 'iban', 'bakiye', 'para_birimi']
    list_filter = ['hesap_tipi', 'aktif_mi']
    search_fields = ['ad', 'hesap_no', 'iban']


@admin.register(BankaHareket)
class BankaHareketAdmin(ImportExportModelAdmin):
    list_display = ['banka', 'hareket_tipi', 'tutar', 'tarih']
    list_filter = ['hareket_tipi', 'tarih']
    search_fields = ['banka__ad', 'aciklama']