from django.contrib import admin
from django.utils.html import format_html
from .models import BarkodSevkiyat, BarkodAdet, BarkodHareket, BarkodYazdirma, SilinenSevkiyatLog


@admin.register(BarkodSevkiyat)
class BarkodSevkiyatAdmin(admin.ModelAdmin):
    list_display = [
        'ihale_sevk', 'toplam_adet', 'toplam_miktar',
        'ortalama_birim', 'durum', 'olusturma_tarihi'
    ]
    list_filter = ['durum', 'olusturma_tarihi']
    search_fields = [
        'ihale_sevk__barkod',
        'ihale_sevk__ihale__kik_no',
        'ihale_sevk__ihale__parti_no',
    ]
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    
    fieldsets = (
        ('Sevkiyat Bağlantısı', {
            'fields': ('ihale_sevk',)
        }),
        ('Özet Bilgiler', {
            'fields': ('toplam_adet', 'toplam_miktar', 'ortalama_birim')
        }),
        ('Durum', {
            'fields': ('durum', 'seri_prefix')
        }),
        ('İşlem', {
            'fields': ('olusturan', 'olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BarkodAdet)
class BarkodAdetAdmin(admin.ModelAdmin):
    list_display = [
        'barkod', 'sira_no', 'barkod_sevkiyat',
        'kalite_durumu', 'durum', 'depo', 'raf'
    ]
    list_filter = ['durum', 'kalite_durumu', 'depo']
    search_fields = ['barkod', 'barkod_sevkiyat__ihale_sevk__ihale__kik_no']
    readonly_fields = ['olusturma_tarihi', 'son_islem_tarihi']
    
    def has_add_permission(self, request):
        # Barkod adetleri sadece otomatik oluşturulur
        return False


@admin.register(BarkodHareket)
class BarkodHareketAdmin(admin.ModelAdmin):
    list_display = [
        'barkod_adet', 'islem_tipi', 'islem_yapan',
        'islem_tarihi', 'yeni_durum'
    ]
    list_filter = ['islem_tipi', 'islem_tarihi']
    search_fields = ['barkod_adet__barkod']
    readonly_fields = ['islem_tarihi']
    
    def has_add_permission(self, request):
        return False


@admin.register(BarkodYazdirma)
class BarkodYazdirmaAdmin(admin.ModelAdmin):
    list_display = [
        'barkod_sevkiyat', 'baslangic_sira', 'bitis_sira',
        'adet', 'yazdiran', 'yazdirma_tarihi'
    ]
    list_filter = ['yazdirma_tarihi']
    readonly_fields = ['yazdirma_tarihi']

@admin.register(SilinenSevkiyatLog)
class SilinenSevkiyatLogAdmin(admin.ModelAdmin):
    list_display = [
        'kik_no', 'parti_no', 'tedarikci', 'barkod_sayisi',
        'silen_kullanici', 'silme_tarihi'
    ]
    list_filter = ['silme_tarihi', 'silen_kullanici']
    search_fields = ['kik_no', 'parti_no', 'tedarikci', 'silme_sebebi']
    readonly_fields = [
        'sevkiyat_id', 'kik_no', 'parti_no', 'tedarikci', 'urun_adi',
        'boy', 'sevk_miktar', 'sevk_adet', 'barkod_sayisi',
        'silme_sebebi', 'silen_kullanici', 'silme_tarihi', 'yedek_ozet'
    ]
    
    def has_add_permission(self, request):
        # Sadece otomatik oluşturulur
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Log silinemez (denetim için)
        return False