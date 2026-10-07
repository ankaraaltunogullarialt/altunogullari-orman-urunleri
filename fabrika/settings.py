# fabrika/settings.py
import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

# ========== GÜVENLİK AYARLARI ==========
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes', 'on')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '16=td=7hp3u0ex07tqjkq0*6@girk-k+=ghb3&5j4)jxm61&oe')

ALLOWED_HOSTS = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    '127.0.0.1,localhost,192.168.1.100,testserver,tomruktakipalt.com,www.tomruktakipalt.com,.ngrok-free.app,.onrender.com'
).split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://tomruktakipalt.com',
    'https://www.tomruktakipalt.com',
    'https://*.onrender.com',
    'https://*.ngrok-free.app',
    'http://192.168.1.100:8000',
    'http://localhost',
]

# ========== STATİK DOSYALAR ==========
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

WSGI_APPLICATION = 'fabrika.wsgi.application'

# ========== LOGGING ==========
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True, parents=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
        },
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': True},
    },
}

# ========== INSTALLED APPS ==========
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'import_export',
    'stok',
    'personel',
    'siparis',
    'finans',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fabrika.middleware.portal_access_middleware',
]

ROOT_URLCONF = 'fabrika.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': str(parsed.port or 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/admin/login/'
LOGOUT_REDIRECT_URL = '/'


# ============================================================
# JAZZMIN AYARLARI
# ============================================================
JAZZMIN_SETTINGS = {
    "site_title": "Altunoğulları Orman Ürünleri Yönetim",
    "site_header": "Altunoğulları Orman Ürünleri",
    "site_brand": "Altunoğulları Orman Ürünleri",
    "welcome_sign": "Hoş Geldiniz",
    "copyright": "Altunoğulları Orman Ürünleri © 2026",
    "show_ui_builder": False,

    # Dashboard linki geri getirildi; yeşil kısa kutu menü yerine sade orijinal üst bar korunur.
    "topmenu_links": [
        {"name": "Dashboard", "url": "/", "new_window": False, "icon": "fas fa-home"},
    ],
    
    "usermenu_links": [
        {"name": "Profil", "url": "/admin/auth/user/", "permissions": ["auth.view_user"]},
        {"model": "auth.user"},
    ],
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "stok.urun": "fas fa-wood",
        "stok.nacekodu": "fas fa-tags",
        "stok.stokhareket": "fas fa-exchange-alt",
        "stok.stokdevir": "fas fa-calendar-alt",
        "stok.depo": "fas fa-warehouse",
        "stok.raf": "fas fa-layer-group",
        "stok.stokbarkod": "fas fa-barcode",
        "stok.ihale": "fas fa-file-contract",
        "stok.ihalesevk": "fas fa-truck",
        "stok.tedarikci": "fas fa-building",
        "stok.tedarikcitipi": "fas fa-tags",
        "stok.tasiyici": "fas fa-truck-moving",
        "stok.tasiyiciarac": "fas fa-truck",
        "stok.tasiyiciodeme": "fas fa-money-bill",
        "personel.personel": "fas fa-user-tie",
        "siparis.siparis": "fas fa-shopping-cart",
        "siparis.musteri": "fas fa-building",
    },
    
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "stok", "personel", "siparis"],
    
    "custom_links": {
        "stok": [
            {
                "name": "📋 Fiili Stok Takip Raporu",
                "url": "/stok/rapor/fiili-stok/",
                "icon": "fas fa-clipboard-list",
            },
        ],
    },
}


JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": True,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
}

MAX_AUTOCOMPLETE_RESULTS = 50
ADMIN_SEARCH_FIELDS = {
    'NACEKodu': ['kod', 'aciklama'],
}