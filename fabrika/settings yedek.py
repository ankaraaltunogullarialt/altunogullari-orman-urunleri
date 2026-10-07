# fabrika/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ========== GÜVENLİK AYARLARI ==========
DEBUG = True

SECRET_KEY = '16=td=7hp3u0ex07tqjkq0*6@girk-k+=ghb3&5j4)jxm61&oe'

# ========== ALLOWED_HOSTS ==========
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '192.168.1.100',
    'sitenizin-adı.com',
    '.ngrok-free.app',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'http://192.168.1.100:8000',
    'http://localhost',
]

# ========== STATİK DOSYALAR ==========
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# ========== MEDIA DOSYALARI ==========
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ========== WSGI ==========
WSGI_APPLICATION = 'fabrika.wsgi.application'

# ========== LOGGING ==========
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
    "site_title": "Orman Fabrikası Yönetim",
    "site_header": "Orman Fabrikası",
    "site_brand": "Orman Yönetim",
    "welcome_sign": "Hoş Geldiniz",
    "copyright": "Orman Fabrikası © 2025",
    "show_ui_builder": False,

    # ★★★ YENİ: ÜST MENÜ ★★★
    "topmenu_links": [
        {"name": "Dashboard", "url": "/", "new_window": False, "icon": "fas fa-home"},
        {"name": "Stok Devirleri", "url": "admin:stok_stokdevir_changelist", "new_window": False, "icon": "fas fa-calendar-alt"},
        {"name": "Fiili Stok Takip", "url": "/stok/rapor/fiili-stok/", "new_window": False, "icon": "fas fa-clipboard-list"},
    ],
    # ★★★ YENİ BİTİŞ ★★★
    
    # ===== ÜST MENÜ =====
    "topmenu_links": [
        # Dashboard
        {"name": "Dashboard", "url": "/", "new_window": False, "icon": "fas fa-home"},
        
        # ===== STOK =====
        {
            "name": "Stok",
            "icon": "fas fa-boxes",
            "models": [
                {"name": "Ürünler", "url": "admin:stok_urun_changelist", "icon": "fas fa-wood"},
                {"name": "NACE Kodları", "url": "admin:stok_nacekodu_changelist", "icon": "fas fa-tags"},
                {"name": "Stok Hareketleri", "url": "admin:stok_stokhareket_changelist", "icon": "fas fa-exchange-alt"},
                {"name": "Stok Devirleri", "url": "admin:stok_stokdevir_changelist", "icon": "fas fa-calendar-alt"},
                {"name": "Depolar", "url": "admin:stok_depo_changelist", "icon": "fas fa-warehouse"},
                {"name": "Raflar", "url": "admin:stok_raf_changelist", "icon": "fas fa-layer-group"},
                {"name": "Stok Barkodları", "url": "admin:stok_stokbarkod_changelist", "icon": "fas fa-barcode"},
            ],
        },
        
        # ===== İHALE =====
        {
            "name": "İhaleler",
            "icon": "fas fa-file-contract",
            "models": [
                {"name": "İhaleler", "url": "admin:stok_ihale_changelist", "icon": "fas fa-file-contract"},
                {"name": "İhale Sevkleri", "url": "admin:stok_ihalesevk_changelist", "icon": "fas fa-truck"},
                {"name": "Tedarikçiler", "url": "admin:stok_tedarikci_changelist", "icon": "fas fa-building"},
                {"name": "Tedarikçi Tipleri", "url": "admin:stok_tedarikcitipi_changelist", "icon": "fas fa-tags"},
            ],
        },
        
        # ===== TAŞIYICI =====
        {
            "name": "Taşıyıcılar",
            "icon": "fas fa-truck-moving",
            "models": [
                {"name": "Taşıyıcılar", "url": "admin:stok_tasiyici_changelist", "icon": "fas fa-truck-moving"},
                {"name": "Taşıyıcı Araçları", "url": "admin:stok_tasiyiciarac_changelist", "icon": "fas fa-truck"},
                {"name": "Taşıyıcı Ödemeleri", "url": "admin:stok_tasiyiciodeme_changelist", "icon": "fas fa-money-bill"},
            ],
        },
        
        # ===== RAPORLAR =====
        {
            "name": "Raporlar",
            "icon": "fas fa-chart-bar",
            "models": [
                {"name": "📊 Rapor Dashboard", "url": "/stok/rapor/dashboard/", "icon": "fas fa-tachometer-alt"},
                {"name": "Fiili Stok Takip", "url": "/stok/rapor/fiili-stok/", "icon": "fas fa-clipboard-list"},
                {"name": "Stok Raporu", "url": "/stok/rapor/stok/", "icon": "fas fa-warehouse"},
                {"name": "Stok Hareket Raporu", "url": "/stok/rapor/stok-hareket/", "icon": "fas fa-exchange-alt"},
                {"name": "İhale Raporu", "url": "/stok/rapor/ihale/", "icon": "fas fa-file-invoice"},
                {"name": "İhale Genel Raporu", "url": "/stok/rapor/ihale-genel/", "icon": "fas fa-file-alt"},
                {"name": "İhale İcmal Raporu", "url": "/stok/rapor/ihale/icmal/", "icon": "fas fa-list"},
                {"name": "KİK İcmal Raporu", "url": "/stok/rapor/ihale-kik-icmal/", "icon": "fas fa-layer-group"},
                {"name": "Boy Analiz Raporu", "url": "/stok/rapor/ihale-boy-analiz/", "icon": "fas fa-ruler"},
                {"name": "Ürün Analiz Raporu", "url": "/stok/rapor/ihale-urun-analiz/", "icon": "fas fa-chart-pie"},
                {"name": "Taşıyıcı Raporu", "url": "/stok/rapor/tasiyici/", "icon": "fas fa-truck"},
                {"name": "Finans Raporu", "url": "/stok/rapor/finans/", "icon": "fas fa-money-bill-wave"},
                {"name": "Üretim Raporu", "url": "/stok/rapor/uretim/", "icon": "fas fa-industry"},
            ],
        },
        
        # ===== YEDEKLEME =====
        {
            "name": "Yedekleme",
            "icon": "fas fa-database",
            "url": "/stok/yedekleme/",
            "new_window": False,
        },
    ],
    
    # ===== KULLANICI MENÜSÜ =====
    "usermenu_links": [
        {"name": "Profil", "url": "/admin/auth/user/", "permissions": ["auth.view_user"]},
        {"model": "auth.user"},
    ],
    
    # ===== İKONLAR =====
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
    "sidebar_disable_expand": False,
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