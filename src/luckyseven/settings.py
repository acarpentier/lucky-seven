"""
Django settings for luckyseven project.
"""

import os
from pathlib import Path
from celery.schedules import crontab
from socket import gethostbyname, gethostname
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,api,host.docker.internal,host.docker.internal:8000', cast=lambda v: [s.strip() for s in v.split(',')])
ALLOWED_HOSTS.append(gethostbyname(gethostname()))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'luckyseven',
]

MIDDLEWARE = [
    'luckyseven.middleware.HealthCheckMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'luckyseven.urls'

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

WSGI_APPLICATION = 'luckyseven.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'luckyseven'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    # Click generator tasks with different affiliate IDs
    'click-generator-1269': {
        'task': 'click_generator',
        'schedule': crontab(minute=0),  # 0 * * * *
        'args': (1269,)
    },
    'click-generator-118': {
        'task': 'click_generator',
        'schedule': crontab(minute=9),  # 9 * * * *
        'args': (118,)
    },
    'click-generator-5010': {
        'task': 'click_generator',
        'schedule': crontab(minute=17),  # 17 * * * *
        'args': (5010,)
    },
    'click-generator-735': {
        'task': 'click_generator',
        'schedule': crontab(minute=26),  # 26 * * * *
        'args': (735,)
    },
    'click-generator-5036': {
        'task': 'click_generator',
        'schedule': crontab(minute=34),  # 34 * * * *
        'args': (5036,)
    },
    'click-generator-5038': {
        'task': 'click_generator',
        'schedule': crontab(minute=43),  # 43 * * * *
        'args': (5038,)
    },
    'click-generator-5058': {
        'task': 'click_generator',
        'schedule': crontab(minute=51),  # 51 * * * *
        'args': (5058,)
    },
    # Click processor - runs every minute
    'click-processor': {
        'task': 'click_processor',
        'schedule': crontab(minute='*'),  # * * * * *
    },
    # Conversion processor - runs every minute
    'conversion-processor': {
        'task': 'conversion_processor',
        'schedule': crontab(minute='*'),  # * * * * *
    },
    # R1 processor - runs daily at 6:00 AM
    'r1-processor': {
        'task': 'r1_processor',
        'schedule': crontab(hour=6, minute=0),  # 0 6 * * *
    },
    # R7 processor - runs daily at 7:00 AM
    'r7-processor': {
        'task': 'r7_processor',
        'schedule': crontab(hour=7, minute=0),  # 0 7 * * *
    },
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
