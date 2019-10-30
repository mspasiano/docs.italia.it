from __future__ import absolute_import
import os

from .testdocsitalia import DocsItaliaTestSettings


class DocsItaliaItResolverTestSettings(DocsItaliaTestSettings):

    if os.environ.get('TRAVIS_DOCSITALIA_DOCKER', False):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'docs',
                'HOST': 'db',
                'PORT': 5432,
                'PASSWORD': 'docs',
                'NAME': 'rtd_itresolver'
            }
        }

    # Override classes
    CLASS_OVERRIDES = {
        'readthedocs.builds.syncers.Syncer': 'readthedocs.builds.syncers.LocalSyncer',
        'readthedocs.core.resolver.Resolver': 'readthedocs.docsitalia.resolver.ItaliaResolver',
        'readthedocs.oauth.services.GitHubService': 'readthedocs.docsitalia.oauth.services.github.DocsItaliaGithubService',  # noqa
    }


DocsItaliaItResolverTestSettings.load_settings(__name__)

if not os.environ.get('DJANGO_SETTINGS_SKIP_LOCAL', False):
    try:
        from .test_local_settings import *  # noqa
    except ImportError:
        pass
