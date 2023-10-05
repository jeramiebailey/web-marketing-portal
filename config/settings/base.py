"""
Base settings to build other settings files upon.
"""

import environ
from datetime import timedelta

ROOT_DIR = environ.Path(__file__) - 3  # (docker_drf_backend/config/settings/base.py - 3 = docker_drf_backend/)
APPS_DIR = ROOT_DIR.path('docker_drf_backend')

env = environ.Env()

READ_DOT_ENV_FILE = env.bool('DJANGO_READ_DOT_ENV_FILE', default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR.path('.env')))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DJANGO_DEBUG', False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = 'America/New_York'
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL'),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'config.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.humanize', # Handy template tags
    'django.contrib.admin',
]
THIRD_PARTY_APPS = [
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',
    'rest_auth.registration',
    'invitations',
    'rest_invitations',
    'anymail',
    'guardian',
    'import_export',
    'simple_history',
]
LOCAL_APPS = [
    'django_celery_beat',
    'docker_drf_backend.users.apps.UsersAppConfig',
    'notifications.apps.NotificationsConfig',
    'api.apps.ApiConfig',
    'organizations.apps.OrganizationsConfig',
    'content_management.apps.ContentManagementConfig',
    'user_onboarding.apps.UserOnboardingConfig',
    'client_onboarding.apps.ClientOnboardingConfig',
    'ticketing.apps.TicketingConfig',
    'user_feedback.apps.UserFeedbackConfig',
    'checklists.apps.ChecklistsConfig',
    'wp_deployments.apps.WpDeploymentsConfig',
    'utilities.apps.UtilitiesConfig',
    'reporting.apps.ReportingConfig',
    'presentations.apps.PresentationsConfig',
    'ui_mapping.apps.UiMappingConfig',
    'account_health.apps.AccountHealthConfig',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {
    'sites': 'docker_drf_backend.contrib.sites.migrations'
}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = 'users.User'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'users:redirect'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = 'account_login'

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
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

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'api.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    # 'api.middleware.CorsMiddleware'
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('staticfiles'))
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(APPS_DIR.path('static')),
]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR('media'))
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
# Use this if you do not have a mailgun account
#EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

ANYMAIL = {
    # (exact settings here depend on your ESP...)
    "MAILGUN_API_KEY": env('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": 'mg.321webmarketing.com',
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"  # or sendgrid.EmailBackend, or...
DEFAULT_FROM_EMAIL = '321 Portal <noreply@mg.321webmarketing.com>'

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = 'admin/'
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("""321 Web Marketing""", 'anthony@321webmarketing.com'),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# Celery
# ------------------------------------------------------------------------------
INSTALLED_APPS += ['docker_drf_backend.taskapp.celery.CeleryAppConfig']
if USE_TZ:
    # http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-timezone
    CELERY_TIMEZONE = TIME_ZONE
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-broker_url
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_backend
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-accept_content
CELERY_ACCEPT_CONTENT = ['json']
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-task_serializer
CELERY_TASK_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#std:setting-result_serializer
CELERY_RESULT_SERIALIZER = 'json'
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERYD_TASK_TIME_LIMIT = 5 * 60 * 2
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-soft-time-limit
# TODO: set to whatever value is adequate in your circumstances
CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 2
# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = env.bool('DJANGO_ACCOUNT_ALLOW_REGISTRATION', True)
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = 'optional'
# https://django-allauth.readthedocs.io/en/latest/configuration.html
#ACCOUNT_ADAPTER = 'docker_drf_backend.users.adapters.AccountAdapter'
ACCOUNT_ADAPTER = 'invitations.models.InvitationsAdapter'
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = 'docker_drf_backend.users.adapters.SocialAccountAdapter'
INVITATIONS_INVITATION_ONLY = True
INVITATIONS_INVITATION_MODEL = 'user_onboarding.CustomInvitation'
INVITATION_SERIALIZER_WRITE = 'api.serializers.InvitationWriteSerializer'
INVITATION_SERIALIZER_READ = 'api.serializers.InvitationReadSerializer'
INVITATIONS_ALLOW_JSON_INVITES = True
INVITATIONS_ACCEPT_INVITE_AFTER_SIGNUP = True
# INVITATIONS_EMAIL_SUBJECT_PREFIX = "beta.321webmarketing.com"
INVITATIONS_EMAIL_SUBJECT_PREFIX = "portal.321webmarketing.com"
ACCOUNT_EMAIL_VERIFICATION = None

# django-compressor
# ------------------------------------------------------------------------------
# https://django-compressor.readthedocs.io/en/latest/quickstart/#installation
INSTALLED_APPS += ['compressor']
STATICFILES_FINDERS += ['compressor.finders.CompressorFinder']
# Your stuff...
# ------------------------------------------------------------------------------


REST_AUTH_SERIALIZERS = {
    'TOKEN_SERIALIZER': 'docker_drf_backend.users.serializers.TokenSerializer',
    'USER_DETAILS_SERIALIZER': 'docker_drf_backend.users.serializers.UserDetailsSerializer',
    'PASSWORD_RESET_SERIALIZER': 'docker_drf_backend.users.serializers.PasswordResetSerializer',
}

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'docker_drf_backend.users.serializers.RegisterSerializer',
}

OLD_PASSWORD_FIELD_ENABLED = True

LOGOUT_ON_PASSWORD_CHANGE = False


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DATETIME_FORMAT': "%Y-%m-%d %H:%M:%S",
    'DATE_FORMAT': "%Y-%m-%d",
    'DEFAULT_METADATA_CLASS': None,
}

if DEBUG:
    REST_FRAMEWORK['DEFAULT_METADATA_CLASS']: 'rest_framework.metadata.SimpleMetadata'

DATE_INPUT_FORMATS = ['%d-%m-%Y']

# from celery.schedules import crontab
# CELERY_BEAT_SCHEDULE = {
#     'check_posted_articles': {
#         'task': 'check_posted_articles',
#         'schedule': crontab(hour=8, minute=0),
#     },
#     'backup_apps': {
#         'task': 'backup_apps',
#         'schedule': crontab(hour=6, minute=0),
#     },
# }


FRONTEND_URL = "http://localhost:3000"

SLACK_TOKEN = env('SLACK_TOKEN', default='')
PRIMARY_SLACK_WEBHOOK_URL = env('PRIMARY_SLACK_WEBHOOK_URL', default='')

DATA_FOR_SEO_LOGIN = env('DATA_FOR_SEO_LOGIN', default='')
DATA_FOR_SEO_PASSWORD = env('DATA_FOR_SEO_PASSWORD', default='')

SECURE_MAIL_HOSTED_ZONE_ID = env('SECURE_MAIL_HOSTED_ZONE_ID', default='')


CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.321webmarketing\.com$",
    r"^http://\w+\localhost\$",
]
CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'https://beta.321webmarketing.com', 'https://portal.321webmarketing.com']
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_EXPOSE_HEADERS = ['Access-Control-Allow-Origin', 'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with']
CORS_ORIGIN_ALLOW = True
CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'https://beta.321webmarketing.com', 'https://portal.321webmarketing.com']
CORS_ORIGIN_WHITELIST = ['http://localhost:3000', 'https://beta.321webmarketing.com', 'https://portal.321webmarketing.com']

from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'Access-Control-Allow-Origin',
    'accept', 
    'accept-encoding', 
    'authorization', 
    'content-type', 
    'dnt', 
    'origin', 
    'user-agent', 
    'x-csrftoken', 
    'x-requested-with'
]

CORS_URLS_REGEX = r'^/api/.*$'

## OLD

# CORS_ORIGIN_ALLOW_ALL = True

# CORS_ALLOWED_ORIGINS = ['http://localhost:3000', 'https://beta.321webmarketing.com']
# CORS_ORIGIN_WHITELIST = ['http://localhost:3000', 'https://beta.321webmarketing.com']
# CORS_ALLOW_CREDENTIALS = True
# CORS_EXPOSE_HEADERS = ['Origin', 'X-Requested-With', 'X-WP-Nonce', 'Content-Type', 'Accept']

# from corsheaders.defaults import default_headers

# CORS_ALLOW_HEADERS = default_headers + (
#     'Access-Control-Allow-Origin',
# )
