# Solfasol

Ankara merkezli online tüketici kooperatifi MVP'si. V1'de admin sabit teklif yayınlar; içerik herkese açıktır, kayıtlı kullanıcılar son başvuruya kadar adet/miktar talebi girer.

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
3. Ziyaretçiler `/` ve `/calendar/` üzerinden içerikleri giriş yapmadan görebilir.
4. Talep girmek isteyen kullanıcılar `/signup/` üzerinden hesap oluşturur.

## Doğrulama

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

API dokümanı: `http://127.0.0.1:8000/api/v1/docs`
