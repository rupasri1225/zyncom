"""
Zyncom — Django Settings
=========================
Works for both local development (.env file) and production (Render env vars).
No hardcoded secrets. All sensitive values come from environment variables.
"""

import os
from pathlib import Path

# ── Base directory ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ───────────────────────────────────────────────────────────────────
# In production: set SECRET_KEY as an environment variable on Render
SECRET_KEY = os.environ.get('SECRET_KEY', 'local-dev-key-change-in-production')

# DEBUG: True locally, False on Render (set DEBUG=False in Render env vars)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Allow Render's domain + localhost
ALLOWED_HOSTS = ['*']  # Render handles SSL termination; restrict further if needed

# ── Installed apps ─────────────────────────────────────────────────────────────
# daphne MUST be first — it replaces Django's dev server with ASGI
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'videoconference_app',
]

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── URLs & ASGI ────────────────────────────────────────────────────────────────
ROOT_URLCONF = 'videoconferencing.urls'
WSGI_APPLICATION = 'videoconferencing.wsgi.application'
ASGI_APPLICATION = 'videoconferencing.asgi.application'

# ── Templates ──────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# ── Database ───────────────────────────────────────────────────────────────────
# Uses SQLite locally. On Render, set DATABASE_URL for PostgreSQL.
DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Django Channels ────────────────────────────────────────────────────────────
# InMemoryChannelLayer for local dev and single-instance Render deployments.
# For multi-instance production, switch to channels_redis.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── Password validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ───────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static files ───────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
<<<<<<< HEAD

# Tell Django where to find static files BEFORE collectstatic copies them
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'videoconference_app', 'static'),
]

# WhiteNoise: CompressedStaticFilesStorage (NOT Manifest — avoids hash issues on Render)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

=======
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'videoconference_app/static')
]
# WhiteNoise: serve compressed static files without a CDN
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
>>>>>>> f1d11ea8869289d81db5f5a4d099aabbb044442c
# ── Media files (user uploads) ─────────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
# ── Default primary key ────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Auth redirects ─────────────────────────────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ── ZegoCloud credentials ──────────────────────────────────────────────────────
# Set these as environment variables on Render (never hardcode)
ZEGO_APP_ID = os.environ.get('ZEGO_APP_ID', '')
ZEGO_SERVER_SECRET = os.environ.get('ZEGO_SERVER_SECRET', '')

# ── Email (optional) ───────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# ── Local dev: load .env file if it exists ─────────────────────────────────────
# This block only runs locally — on Render, env vars are set in the dashboard
try:
    from decouple import config as _config
    # Override with .env values if available (local dev only)
    SECRET_KEY = _config('SECRET_KEY', default=SECRET_KEY)
    DEBUG = _config('DEBUG', default=str(DEBUG), cast=lambda v: v == 'True')
    ZEGO_APP_ID = _config('ZEGO_APP_ID', default=ZEGO_APP_ID)
    ZEGO_SERVER_SECRET = _config('ZEGO_SERVER_SECRET', default=ZEGO_SERVER_SECRET)
    EMAIL_HOST_USER = _config('EMAIL_HOST_USER', default=EMAIL_HOST_USER)
    EMAIL_HOST_PASSWORD = _config('EMAIL_HOST_PASSWORD', default=EMAIL_HOST_PASSWORD)
except ImportError:
    pass  # python-decouple not installed — use os.environ values only
