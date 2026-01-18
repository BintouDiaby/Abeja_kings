from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-change-me'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
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

ROOT_URLCONF = 'backend_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [ BASE_DIR / 'templates' ],
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

WSGI_APPLICATION = 'backend_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = [
    'core.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [ BASE_DIR / 'static' ]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_URL = '/accounts/login/'
# After login, redirect users to a small handler that routes them based on role
LOGIN_REDIRECT_URL = '/post-login/'
LOGOUT_REDIRECT_URL = '/'  # après déconnexion, rediriger vers la page d'accueil

# Session configuration: control how long authenticated sessions persist.
# By default sessions will expire at browser close (unless 'remember_me' is used).
# Set a reasonable persistent duration (30 days) when 'remember_me' is requested.
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days in seconds
# Refresh session expiry on each request so activity keeps the user logged in
SESSION_SAVE_EVERY_REQUEST = True
# Default behavior: do not force expire at browser close globally (we control per-login)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ----- Email configuration -------------------------------------------------
# By default (DEBUG=True) use the console backend so emails are printed to
# the runserver console. For production, set the environment variables
# below (EMAIL_BACKEND to 'django.core.mail.backends.smtp.EmailBackend' or
# leave empty to use the SMTP backend) and provide SMTP credentials.
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# If an explicit EMAIL_BACKEND is provided through env, use it. Otherwise
# in DEBUG use console backend, else SMTP backend.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False').lower() in ('1', 'true', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Optional: when using some SMTP providers you may want to set this
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

# If using the file-based backend for development, this is where files will be written.
# Default: backend/tmp/emails (relative to BASE_DIR)
EMAIL_FILE_PATH = os.environ.get('EMAIL_FILE_PATH', str(BASE_DIR / 'tmp' / 'emails'))


# Logging: show debug output for authentication backend during development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'core.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core.views': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

