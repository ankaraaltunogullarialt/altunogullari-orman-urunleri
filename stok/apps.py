from django.apps import AppConfig


class StokConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stok'
    verbose_name = 'Stok Yönetimi'

    def ready(self):
        """Signals'leri yükle"""
        import stok.signals  # noqa