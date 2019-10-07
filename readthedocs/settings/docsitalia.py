from .dev import CommunityDevSettings


CommunityDevSettings.load_settings(__name__)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '',
        'PASSWORD': '',
        'NAME': 'docsitalia'
    }
}