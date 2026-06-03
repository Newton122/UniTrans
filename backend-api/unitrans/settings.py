from pathlib import Path
from datetime import timedelta
import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'corsheaders',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.lines',
    'apps.schedules',
    'apps.buses',
    'apps.subscriptions',
    'apps.trips',
    'apps.incidents',
    'apps.notifications',
    'apps.reports',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'unitrans.middleware.LogRequestBodyMiddleware',
]

ROOT_URLCONF = 'unitrans.urls'

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

WSGI_APPLICATION = 'unitrans.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        default='postgresql://postgres:NeUrOViSion_AI@localhost:5432/unitrans_db',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'unitrans.exception_handler.custom_exception_handler',
}

# SimpleJWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
}

# drf-spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'UniTrans API',
    'DESCRIPTION': (
        'University Transport Management System API. '
        'Provides endpoints for student subscriptions, trip scheduling, '
        'seat assignments, incident reporting, and notifications.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication — register, login, token refresh'},
        {'name': 'accounts', 'description': 'Student and user profile management'},
        {'name': 'lines', 'description': 'Bus lines, stations, and timetables'},
        {'name': 'schedules', 'description': 'Schedule management'},
        {'name': 'buses', 'description': 'Bus fleet and bus-to-line assignments'},
        {'name': 'subscriptions', 'description': 'Student line subscriptions and history'},
        {'name': 'trips', 'description': 'Trip management, rows, and seat assignments'},
        {'name': 'incidents', 'description': 'Incident reporting and resolution'},
        {'name': 'notifications', 'description': 'Alerts and notifications'},
        {'name': 'reports', 'description': 'Aggregated system reports (Manager only)'},
    ],
}

# CORS
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in config(
        'CORS_ALLOWED_ORIGINS',
        default=(
            'https://unitrans.onrender.com,'
            'https://frontend-driver.onrender.com,'
            'https://frontend-manager.onrender.com,'
            'https://frontend-student.onrender.com,'
            'https://frontent-driver.onrender.com,'
            'https://frontent-manager.onrender.com,'
            'https://frontent-student.onrender.com,'
            'http://localhost:3000,'
            'http://127.0.0.1:3000,'
            'http://localhost:3001,'
            'http://127.0.0.1:3001,'
            'http://localhost:3002,'
            'http://127.0.0.1:3002,'
            'http://localhost:5173'
        ),
    ).split(',')
]
CORS_ALLOW_CREDENTIALS = True
# Temporary: allow all origins for debugging CORS issues
CORS_ALLOW_ALL_ORIGINS = True
