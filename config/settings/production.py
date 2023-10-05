import logging

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env('DJANGO_SECRET_KEY')
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
#ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost:8000'])
ALLOWED_HOSTS = ['api.321webmarketing.com','tasks.321webmarketing.com']

# DATABASES
# ------------------------------------------------------------------------------
DATABASES['default'] = env.db('DATABASE_URL')  # noqa F405
DATABASES['default']['ATOMIC_REQUESTS'] = True  # noqa F405
DATABASES['default']['CONN_MAX_AGE'] = env.int('CONN_MAX_AGE', default=60)  # noqa F405

# CACHES
# ------------------------------------------------------------------------------

use_aws_redis = env('USE_AWS_REDIS')
local_redis_url = env('LOCAL_REDIS_URL')
aws_redis_url = env('AWS_REDIS_URL')

default_redis_url = local_redis_url
if use_aws_redis:
    default_redis_url = aws_redis_url

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': default_redis_url,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # Mimicing memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            'IGNORE_EXCEPTIONS': False,
        }
    }
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool('DJANGO_SECURE_HSTS_PRELOAD', default=True)

### I disabled this
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
# SECURE_CONTENT_TYPE_NOSNIFF = env.bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', default=True)

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True

### I changed this from 'DENY'
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = 'ALLOWALL'

# STORAGES
# ------------------------------------------------------------------------------
# https://django-storages.readthedocs.io/en/latest/#installation
INSTALLED_APPS += ['storages']  # noqa F405
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_ACCESS_KEY_ID = env('DJANGO_AWS_ACCESS_KEY_ID')
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = env('DJANGO_AWS_SECRET_ACCESS_KEY')
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_STORAGE_BUCKET_NAME = env('DJANGO_AWS_STORAGE_BUCKET_NAME')
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
_AWS_EXPIRY = 60 * 60 * 24 * 7
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': f'max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate',
}
AWS_DEFAULT_ACL = None

# STATIC
# ------------------------

STATICFILES_STORAGE = "config.settings.production.StaticRootS3Boto3Storage"
STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/"

# MEDIA
# ------------------------------------------------------------------------------

# region http://stackoverflow.com/questions/10390244/
# from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402
# StaticRootS3BotoStorage = lambda: S3Boto3Storage(location='static')  # noqa
# MediaRootS3BotoStorage = lambda: S3Boto3Storage(location='media', file_overwrite=False)  # noqa
# # endregion
# DEFAULT_FILE_STORAGE = 'config.settings.production.MediaRootS3BotoStorage'
# MEDIA_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/media/'
# MEDIA_ROOT = MEDIA_URL

# from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402


# class StaticRootS3Boto3Storage(S3Boto3Storage):
#     location = "static"
#     default_acl = "public-read"


# class MediaRootS3Boto3Storage(S3Boto3Storage):
#     location = "media"
#     file_overwrite = False

from config.storages import CustomS3Boto3Storage  # noqa E402


class StaticRootS3Boto3Storage(CustomS3Boto3Storage):
    location = "static"
    default_acl = "public-read"
    file_overwrite = True


class MediaRootS3Boto3Storage(CustomS3Boto3Storage):
    location = "media"
    default_acl = 'public-read'
    file_overwrite = True


# endregion
DEFAULT_FILE_STORAGE = "config.settings.production.MediaRootS3Boto3Storage"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/"

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]['OPTIONS']['loaders'] = [  # noqa F405
    (
        'django.template.loaders.cached.Loader',
        [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]
    ),
]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    'DJANGO_DEFAULT_FROM_EMAIL',
    default='docker_drf_backend <noreply@localhost:8000>'
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env('DJANGO_EMAIL_SUBJECT_PREFIX', default='[docker_drf_backend]')

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env('DJANGO_ADMIN_URL')

# Anymail (Mailgun)
# ------------------------------------------------------------------------------
# https://anymail.readthedocs.io/en/stable/installation/#installing-anymail
# INSTALLED_APPS += ['anymail']  # noqa F405
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
# https://anymail.readthedocs.io/en/stable/installation/#anymail-settings-reference
ANYMAIL = {
    'MAILGUN_API_KEY': env('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': env('MAILGUN_DOMAIN')
}

# Gunicorn
# ------------------------------------------------------------------------------
INSTALLED_APPS += ['gunicorn']  # noqa F405

# django-compressor
# ------------------------------------------------------------------------------
# https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_ENABLED
COMPRESS_ENABLED = env.bool('COMPRESS_ENABLED', default=True)
# https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_STORAGE
COMPRESS_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_URL
COMPRESS_URL = STATIC_URL

# Collectfast
# ------------------------------------------------------------------------------
# https://github.com/antonagestam/collectfast#installation
# INSTALLED_APPS = ['collectfast'] + INSTALLED_APPS  # noqa F405
# AWS_PRELOAD_METADATA = True

# raven
# ------------------------------------------------------------------------------
# https://docs.sentry.io/clients/python/integrations/django/
INSTALLED_APPS += ['raven.contrib.django.raven_compat']  # noqa F405
# MIDDLEWARE = ['raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware'] + MIDDLEWARE

MIDDLEWARE += ['raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware']

# Sentry
# ------------------------------------------------------------------------------
SENTRY_DSN = env('SENTRY_DSN')
SENTRY_CLIENT = env('DJANGO_SENTRY_CLIENT', default='raven.contrib.django.raven_compat.DjangoClient')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'celery': {
            'level': 'ERROR',
            'handlers': ['sentry', 'console'],
            'propagate': False
        },
        'django.security.DisallowedHost': {
            'level': 'WARNING',
            'handlers': ['console', 'sentry'],
            'propagate': False,
        },
    },
}

SENTRY_CELERY_LOGLEVEL = env.int('DJANGO_SENTRY_LOG_LEVEL', logging.ERROR)
RAVEN_CONFIG = {
    'dsn': SENTRY_DSN
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'api.renderers.NoHTMLFormBrowsableAPIRenderer'
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
    'DATE_FORMAT': "%Y-%m-%d",
}

# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = False
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = False


TASK_SERVER = env('TASK_SERVER', default=False)

from celery.schedules import crontab

if TASK_SERVER:
    CELERY_BEAT_SCHEDULE = {
        'check_posted_articles': {
            'task': 'check_posted_articles',
            'schedule': crontab(hour=8, minute=0),
        },
        'check_completed_projects': {
            'task': 'check_completed_projects',
            'schedule': crontab(hour=8, minute=0),
        },
        'backup_apps': {
            'task': 'backup_apps',
            'schedule': crontab(hour=6, minute=0),
        },
        'send_weekly_review_email': {
            'task': 'send_weekly_review_email',
            'schedule': crontab(hour=8, minute=30, day_of_week=1),
        },
        'scheduled_create_monthly_reports': {
            'task': 'scheduled_create_monthly_reports',
            'schedule': crontab(hour=2, minute=00),
        },
        'scheduled_validate_created_report_status': {
            'task': 'scheduled_validate_created_report_status',
            'schedule': crontab(hour=6, minute=00),
        },
        'scheduled_create_monthly_report_presentations': {
            'task': 'scheduled_create_monthly_report_presentations',
            'schedule': crontab(hour=8, minute=00),
        },
        'scheduled_query_unsent_reports': {
            'task': 'scheduled_query_unsent_reports',
            'schedule': crontab(hour=8, minute=00),
        },
        'pull_all_account_data': {
            'task': 'pull_all_account_data',
            'schedule': crontab(hour=7, minute=00, day_of_week=1),
        },
        'populate_daily_article_history_set': {
            'task': 'populate_daily_article_history_set',
            'schedule': crontab(hour=5, minute=00),
        },
        'send_due_soon_reminders': {
            'task': 'send_due_soon_reminders',
            'schedule': crontab(hour=7, minute=30),
        }
    }
else:
    CELERY_BEAT_SCHEDULE = {}


# FRONTEND_URL = env('FRONTEND_URL', default='https://beta.321webmarketing.com')
FRONTEND_URL = env('FRONTEND_URL', default='https://portal.321webmarketing.com')
BACKEND_URL = env('BACKEND_URL', default='https://api.321webmarketing.com')
