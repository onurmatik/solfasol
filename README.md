# Solfasol

Ankara merkezli, davetle büyüyen online tüketici kooperatifi MVP'si. V1'de admin sabit teklif yayınlar; üyeler deadline'a kadar adet/miktar talebi girer.

## Kurulum

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Uygulama varsayılan olarak `http://127.0.0.1:8000/` adresinde çalışır.

## İlk kullanım

1. Admin kullanıcısı ile `/admin/` üzerinden giriş yapın.
2. Ürün kategorisi, ürün, teslim noktası, tedarikçi kaynağı ve teklifleri Django admin üzerinden oluşturun.
4. `/invitations/` üzerinden reusable davet linki oluşturun.
5. Davet linkiyle gelen kullanıcılar otomatik aktif üye olur; kullanılan link ve davet eden üye profilde izlenir.

## Doğrulama

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

API dokümanı: `http://127.0.0.1:8000/api/v1/docs`
