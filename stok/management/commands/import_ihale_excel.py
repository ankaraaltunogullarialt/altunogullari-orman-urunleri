import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stok.models import Ihale, IhaleParti, Tedarikci
from datetime import datetime

class Command(BaseCommand):
    help = 'Excel dosyasından ihale verilerini içe aktarır'

    def add_arguments(self, parser):
        parser.add_argument('excel_dosyasi', type=str, help='Excel dosyasının yolu')

    def handle(self, *args, **options):
        dosya_yolu = options['excel_dosyasi']
        self.stdout.write(f"Excel dosyası okunuyor: {dosya_yolu}")
        
        # Excel'i oku
        df = pd.read_excel(dosya_yolu, sheet_name='İHALEDEN ALINAN TOMRUK', header=5)
        
        # Boş satırları temizle
        df = df.dropna(how='all')
        df = df[df['YER'].notna()]
        
        # Benzersiz ihaleleri bul (YER + PARTİ + ALIŞ TARİHİ kombinasyonu)
        # Ancak Excel'de her satır bir parti. Aynı ihaleye ait birden fazla parti olabilir.
        # Bu nedenle, önce ihaleleri oluşturup sonra partileri ekleyeceğiz.
        # Basitlik açısından, her satırı ayrı bir ihale olarak ekleyelim (parti no'yu ihale no olarak kullanabiliriz).
        # Veya YER + PARTİ + ALIŞ TARİHİ'ne göre gruplayalım.
        
        # Tedarikçi'yi bul veya oluştur (YER'e göre)
        tedarikci, _ = Tedarikci.objects.get_or_create(
            unvan=df.iloc[0]['YER'],  # İlk satırdaki YER'i kullan
            defaults={'aktif_mi': True}
        )
        
        for index, row in df.iterrows():
            # Verileri temizle
            yer = row['YER']
            alis_tarihi = row['ALIŞ TARİHİ']
            parti_no = str(row['PARTİ']).strip()
            m3 = row['M3']
            fiyat = row['FİYATI']
            cins_istif = row['CİNS VE İSTİF NO'] if pd.notna(row['CİNS VE İSTİF NO']) else ''
            depo = row['DEPO'] if pd.notna(row['DEPO']) else ''
            adet = row['ADET'] if pd.notna(row['ADET']) else 0
            boy = row['BOY'] if pd.notna(row['BOY']) else ''
            durum = row['DURUM'] if pd.notna(row['DURUM']) else ''
            
            # Tarih dönüşümü
            if isinstance(alis_tarihi, datetime):
                alis_tarihi_date = alis_tarihi.date()
            else:
                alis_tarihi_date = alis_tarihi  # Zaten date olabilir
            
            # İhale oluştur (Parti No'yu ihale no olarak kullanma)
            # Daha iyisi: YER + ALIŞ TARİHİ + PARTİ'ye göre benzersiz ihale oluştur
            # Şimdilik her satır için yeni bir ihale oluşturalım (basitlik)
            ihale_no = f"IHA-{parti_no}"  # Parti no'yu kullan
            
            # Tedarikçi'yi bul (YER'e göre)
            tedarikci, _ = Tedarikci.objects.get_or_create(
                unvan=yer,
                defaults={'aktif_mi': True}
            )
            
            # İhale'yi bul veya oluştur
            ihale, created = Ihale.objects.get_or_create(
                kik_no=parti_no,  # KIK no olarak parti no'yu kullan
                defaults={
                    'ihale_no': ihale_no,
                    'tedarikci': tedarikci,
                    'urun_adi': 'Tomruk',  # Sabit
                    'toplam_miktar': m3,  # Kalan miktar
                    'toplam_adet': adet,
                    'birim_fiyat': fiyat,
                    'durum': 'devam_ediyor',
                    'ihale_tarihi': alis_tarihi_date,
                    'aciklama': f"Excel'den içe aktarıldı: {yer}"
                }
            )
            
            if created:
                self.stdout.write(f"Yeni ihale oluşturuldu: {ihale.ihale_no}")
            else:
                self.stdout.write(f"İhale zaten var: {ihale.ihale_no}")
            
            # Parti'yi oluştur
            parti, created = IhaleParti.objects.get_or_create(
                ihale=ihale,
                parti_no=parti_no,
                defaults={
                    'gelen_miktar': m3,
                    'adet': adet,
                    'kalan_miktar': m3,
                    'kalan_adet': adet,
                    'gelis_tarihi': alis_tarihi_date,
                    'boy': boy,
                    'cins_istif_no': cins_istif,
                    'durum_aciklama': durum,
                    'notlar': f"Depo: {depo}"
                }
            )
            
            if created:
                self.stdout.write(f"Parti eklendi: {parti.parti_no}")
            else:
                self.stdout.write(f"Parti zaten var: {parti.parti_no}")
        
        self.stdout.write(self.style.SUCCESS('Veri aktarımı tamamlandı!'))