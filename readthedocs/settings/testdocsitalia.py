import os

from .test import CommunityTestSettings


CommunityTestSettings.load_settings(__name__)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'PREFIX': 'docs',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USERNAME': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '',
        'PASSWORD': '',
        'NAME': 'test_docsitalia'
    }
}


if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        from .test_local_settings import *  # noqa
    except ImportError:
        pass
