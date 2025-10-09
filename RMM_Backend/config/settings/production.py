from .base import *

# SECURITY WARNING: don't run with debug turned on in production!


ALLOWED_HOSTS = [
    "127.0.0.1", 
    "localhost",
    # 🛑 Agregados para el despliegue de Nginx 🛑
    "revista.metaminingmedia.com",
    "metaminingmedia.com",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# CORS / CSRF
CORDS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # 🛑 Agregados para el despliegue de Nginx (HTTPS) 🛑
    "https://revista.metaminingmedia.com",
    "https://metaminingmedia.com",
]

SITE_URL = "https://revista.metaminingmedia.com"
