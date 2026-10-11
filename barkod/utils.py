# barkod/utils.py
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def qr_icerik_olustur(barkod_adet):
    """
    Barkod adedi için QR içeriği oluştur.
    Format: İnsan okuyabilir metin (KİK, Parti, İstif, Tedarikçi, Depo vb.)
    """
    sevkiyat = barkod_adet.barkod_sevkiyat
    ihale_sevk = sevkiyat.ihale_sevk
    ihale = ihale_sevk.ihale
    
    # Depo/Raf bilgisi
    depo_adi = barkod_adet.depo.ad if barkod_adet.depo else '-'
    raf_kodu = barkod_adet.raf.kod if barkod_adet.raf else '-'
    
    # İçerik
    icerik = (
        f"BARKOD:{barkod_adet.barkod}\n"
        f"KIK:{ihale.kik_no or '-'}\n"
        f"PARTI:{ihale.parti_no or '-'}\n"
        f"ISTIF:{ihale.istif_no or '-'}\n"
        f"TEDARIKCI:{ihale.tedarikci.unvan if ihale.tedarikci else '-'}\n"
        f"URUN:{ihale.urun_adi or '-'}\n"
        f"BOY:{ihale.boy or '-'}\n"
        f"MIKTAR:{barkod_adet.olcum_miktar or 0}m3\n"
        f"DEPO:{depo_adi}\n"
        f"RAF:{raf_kodu}"
    )
    return icerik


def qr_kod_uret(barkod_adet, kaydet=True, box_size=12):
    """
    Barkod adedi için QR kod resmi üret.
    Eski QR varsa siler, üzerine yazar.
    """
    icerik = qr_icerik_olustur(barkod_adet)
    
    # ★★★ ESKİ QR'I SİL ★★★
    if barkod_adet.qr_kod:
        try:
            barkod_adet.qr_kod.delete(save=False)
        except Exception:
            pass
    
    # QR oluştur
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=2,
    )
    qr.add_data(icerik)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    dosya_adi = f'qr_{barkod_adet.barkod}.png'
    barkod_adet.qr_kod.save(dosya_adi, ContentFile(buffer.read()), save=False)
    barkod_adet.qr_icerik = icerik
    
    if kaydet:
        barkod_adet.save(update_fields=['qr_kod', 'qr_icerik'])
    
    return barkod_adet.qr_kod