from django.core.management.base import BaseCommand
from stok.utils import gunluk_snapshot_olustur


class Command(BaseCommand):
    help = 'Günlük snapshot oluştur (stok, ihale, finans durumu)'
    
    def handle(self, *args, **options):
        snapshot = gunluk_snapshot_olustur()
        self.stdout.write(
            self.style.SUCCESS(f'✅ Snapshot oluşturuldu: {snapshot.tarih}')
        )