# Altunoğulları Portal / Public Site Stable Snapshot

Tarih: 2026-10-07

Bu klasör, istenen son stabil tasarım ve davranış setini yedekler.

## Sabitlenen durum

- Public site root uses the corporate Altunoğulları header and landing layout.
- Admin logout redirects to the public site home (`/`).
- Portal logout redirects to the public site home (`/`) as well.
- Portal login page is simplified and does not include the large emblem; the large brand block remains on the public landing page.
- Main files involved:
  - `fabrika/urls.py`
  - `templates/base.html`
  - `templates/site_entry.html`
  - `templates/portal/login.html`
  - `static/css/custom.css`

## Doğrulama

Django kontrol komutu çalıştırıldı ve şu çıktı alındı:

- `./venv/Scripts/python.exe manage.py check`
- Sonuç: `System check identified no issues (0 silenced).`

## Not

Bu klasör, daha sonra yapılacak değişikliklerde geri dönüş için referans olarak tutulur.
