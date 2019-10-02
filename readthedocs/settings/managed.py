# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from .dev import CommunityDevSettings


class LocalSettings(CommunityDevSettings):

    RTD_LATEST = 'bozza'
    RTD_STABLE = 'stabile'

    ES_HOSTS = 'http://192.168.93.67:9200'

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'PREFIX': 'docs',
        }
    }

    @property
    def INSTALLED_APPS(self):  # noqa
        apps = super(LocalSettings, self).INSTALLED_APPS
        # Insert our depends above RTD applications, after guaranteed third
        # party package
        apps.insert(apps.index('rest_framework'), 'docs_italia_convertitore_web')

        apps.insert(apps.index('rest_framework'), 'raven.contrib.django.raven_compat')

        return apps

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'USER': 'postgres',
            'HOST': '',
            'PORT': '',
            'PASSWORD': '',
            'NAME': 'docsitalia'
        }
    }

    # Override classes
    CLASS_OVERRIDES = {
        'readthedocs.builds.syncers.Syncer': 'readthedocs.builds.syncers.LocalSyncer',
        'readthedocs.core.resolver.Resolver': 'readthedocs.docsitalia.resolver.ItaliaResolver',
        'readthedocs.oauth.services.GitHubService':
            'readthedocs.docsitalia.oauth.services.github.DocsItaliaGithubService',
    }

    CELERY_ALWAYS_EAGER = False
    BROKER_URL = 'redis://localhost:6379/13'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/13'

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'falbala'

    CORS_ORIGIN_REGEX_WHITELIST = ['http://example.com']

LocalSettings.load_settings(__name__)
