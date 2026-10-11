from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IhaleSevk


@receiver(post_save, sender=IhaleSevk)
def ihale_sevk_barkod_olustur(sender, instance, created, **kwargs):
    """
    Yeni IhaleSevk oluşturulduğunda otomatik BarkodSevkiyat oluştur
    """
    if created:
        from barkod.models import BarkodSevkiyat
        BarkodSevkiyat.objects.get_or_create(
            ihale_sevk=instance,
            defaults={
                'durum': 'beklemede',
                'toplam_adet': 0,
                'toplam_miktar': 0,
            }
        )