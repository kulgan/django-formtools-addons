# -*- coding: utf-8 -*-
import os
import environ

root = environ.Path(__file__) - 2

env = environ.Env(
    DEBUG=(bool, True),
)

DEBUG = env('DEBUG')

# noinspection PyCallingNonCallable
SITE_ROOT = root()

DATABASES = {
    'default': env.db(default='sqlite:///%s/dev.sqlite.db' % SITE_ROOT),
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'formtools',
    'formtools_addons',

    'testapp',
]

ROOT_URLCONF = 'accordeon_wizard.urls'

SECRET_KEY = 'spam-spam-spam-spam'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'spam-and-eggs'
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',

    'formtools_addons.middleware.JSONMiddleware'
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(SITE_ROOT, 'accordeon_wizard/templates')
        ]
        ,
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

SITE_ID = 1

MEDIA_ROOT = 'media'
STATIC_ROOT = 'static'

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'formtools_addons.wizard.wizardapi': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
