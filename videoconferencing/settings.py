"""
Zyncom - Django Settings
========================
Simple, beginner-friendly settings for the Zyncom collaboration platform.
Uses InMemoryChannelLayer for local development (no Redis needed).
Swap to channels_redis for production (see comment below).
"""

from pathlib import Path
import os
from decouple import config

# ─── Base directory ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

# ─── Installed apps ───────────────────────────────────────────────────────────
# IMPORTANT: 'daphne' MUST be first so it handles ASGI correctly.
INSTALLED_APPS = [
    'daphne',                               # Must be FIRST (ASGI server)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',                             # Django Channels (WebSockets)
    'videoconference_app',                  # Our main app
]

# ─── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',    # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ─── URL & ASGI/WSGI ──────────────────────────────────────────────────────────
ROOT_URLCONF = 'videoconferencing.urls'
WSGI_APPLICATION = 'videoconferencing.wsgi.application'
ASGI_APPLICATION = 'videoconferencing.asgi.application'  # Points to our ASGI app

# ─── Templates ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],          # Templates are found via APP_DIRS=True
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

# ─── Database ─────────────────────────────────────────────────────────────────
# Uses SQLite by default (stored in BASE_DIR/db.sqlite3).
# Set DATABASE_URL in .env for PostgreSQL in production.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── Django Channels (WebSockets) ─────────────────────────────────────────────
# InMemoryChannelLayer: works out of the box, no Redis needed for development.
# For production, replace with:
#   'BACKEND': 'channels_redis.core.RedisChannelLayer',
#   'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ─── Password validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─── Media files (user uploads) ───────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Default primary key ──────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Authentication redirects ─────────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ─── ZegoCloud credentials ────────────────────────────────────────────────────
# Add ZEGO_APP_ID and ZEGO_SERVER_SECRET to your .env file.
ZEGO_APP_ID = config('ZEGO_APP_ID', default='')
ZEGO_SERVER_SECRET = config('ZEGO_SERVER_SECRET', default='')

# ─── Email (optional) ─────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
