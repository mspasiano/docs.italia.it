import logging

from django.http import Http404
from django.test import TestCase
from django.test.utils import override_settings
from django_dynamic_fixture import fixture, get

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.redirects.models import Redirect


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False, APPEND_SLASH=False)
class RedirectTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        logging.disable(logging.DEBUG)
        self.client.login(username='eric', password='test')
        pip = Project.objects.get(slug='pip')
        pip.versions.create_latest()

    def test_proper_url_no_slash(self):
        r = self.client.get('/docs/pip')
        self.assertEqual(r.status_code, 404)

    def test_proper_url(self):
        r = self.client.get('/docs/pip/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://readthedocs.org/docs/pip/en/latest/',
        )

    # Specific Page Redirects
    def test_proper_page_on_main_site(self):
        r = self.client.get('/docs/pip/page/test.html')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://readthedocs.org/docs/pip/en/latest/test.html',
        )

    def test_page_redirect_with_query_params(self):
        r = self.client.get('/docs/pip/page/test.html?foo=bar')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://readthedocs.org/docs/pip/en/latest/test.html?foo=bar'
        )

    # If slug is neither valid lang nor valid version, it should 404.
    # TODO: This should 404 directly, not redirect first
    def test_improper_url_with_nonexistent_slug(self):
        r = self.client.get('/docs/pip/nonexistent/')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_filename_only(self):
        r = self.client.get('/docs/pip/test.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_dir_file(self):
        r = self.client.get('/docs/pip/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_dir_subdir_file(self):
        r = self.client.get('/docs/pip/nonexistent_dir/subdir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_lang_file(self):
        r = self.client.get('/docs/pip/en/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_lang_subdir_file(self):
        r = self.client.get('/docs/pip/en/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    def test_improper_url_version_dir_file(self):
        r = self.client.get('/docs/pip/latest/nonexistent_dir/bogus.html')
        self.assertEqual(r.status_code, 404)

    # Subdomains
    @override_settings(USE_SUBDOMAIN=True)
    def test_proper_subdomain(self):
        r = self.client.get('/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_root_redirect_with_query_params(self):
        r = self.client.get('/?foo=bar', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.readthedocs.org/en/latest/?foo=bar'
        )

    # Specific Page Redirects
    @override_settings(USE_SUBDOMAIN=True)
    def test_proper_page_on_subdomain(self):
        r = self.client.get('/page/test.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.readthedocs.org/en/latest/test.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_improper_subdomain_filename_only(self):
        r = self.client.get('/test.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 404)


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class RedirectAppTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.client.login(username='eric', password='test')
        self.pip = Project.objects.get(slug='pip')
        self.pip.versions.create_latest()

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_prefix_infinite(self):
        """
        Avoid infinite redirects.

        If the URL hit is the same that the URL returned for redirection, we
        return a 404.

        These examples comes from this issue:
          * https://github.com/rtfd/readthedocs.org/issues/4673
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='prefix',
            from_url='/',
        )
        r = self.client.get('/redirect.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/redirect.html',
        )

        r = self.client.get('/redirect/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/redirect/',
        )

        r = self.client.get('/en/latest/redirect/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 404)

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_prefix_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='prefix',
            from_url='/',
        )

        r = self.client.get('http://testserver/http://my.host/path.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/http://my.host/path.html',
        )

        r = self.client.get('http://testserver//my.host/path.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/my.host/path.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_sphinx_htmldir_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_htmldir',
        )

        r = self.client.get('http://testserver/http://my.host/path.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/http://my.host/path/',
        )

        r = self.client.get('http://testserver//my.host/path.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/my.host/path/',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_sphinx_html_crossdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_html',
        )

        r = self.client.get('http://testserver/http://my.host/path/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/http://my.host/path.html',
        )

        r = self.client.get('http://testserver//my.host/path/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/my.host/path.html',
        )

    def test_redirect_sphinx_htmldir_crossdomain_nosubdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_htmldir',
        )

        r = self.client.get('/docs/pip/http://my.host/path.html')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://testserver/docs/pip/en/latest/http://my.host/path/',
        )

        r = self.client.get('/docs/pip//my.host/path.html')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://testserver/docs/pip/en/latest/my.host/path/',
        )

    def test_redirect_sphinx_html_crossdomain_nosubdomain(self):
        """
        Avoid redirecting to an external site unless the external site is in to_url
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_html',
        )

        r = self.client.get('/docs/pip//http://my.host/path/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://testserver/docs/pip/en/latest/http://my.host/path.html',
        )

        r = self.client.get('/docs/pip//my.host/path/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://testserver/docs/pip/en/latest/my.host/path.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_root(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='prefix', from_url='/woot/',
        )
        r = self.client.get('/woot/faq.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/faq.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_page(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='page',
            from_url='/install.html', to_url='/tutorial/install.html',
        )
        r = self.client.get('/install.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/tutorial/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_with_query_params(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='page',
            from_url='/install.html', to_url='/tutorial/install.html'
        )
        r = self.client.get(
            '/install.html?foo=bar', HTTP_HOST='pip.readthedocs.org'
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.readthedocs.org/en/latest/tutorial/install.html?foo=bar'
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_exact(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='exact',
            from_url='/en/latest/install.html', to_url='/en/latest/tutorial/install.html',
        )
        r = self.client.get('/en/latest/install.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/tutorial/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_exact_with_rest(self):
        """
        Exact redirects can have a ``$rest`` in the ``from_url``.

        Use case: we want to deprecate version ``2.0`` and replace it by
        ``3.0``. We write an exact redirect from ``/en/2.0/$rest`` to
        ``/en/3.0/``.
        """
        Redirect.objects.create(
            project=self.pip, redirect_type='exact',
            from_url='/en/latest/$rest', to_url='/en/version/', # change version
        )
        r = self.client.get('/en/latest/guides/install.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/version/guides/install.html',
        )

        Redirect.objects.create(
            project=self.pip, redirect_type='exact',
            from_url='/es/version/$rest', to_url='/en/master/', # change language and version
        )
        r = self.client.get('/es/version/guides/install.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/master/guides/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_inactive_version(self):
        """
        Inactive Version (``active=False``) should redirect properly.

        The function that servers the page should return 404 when serving a page
        of an inactive version and the redirect system should work.
        """
        version = get(
            Version,
            slug='oldversion',
            project=self.pip,
            active=False,
        )
        Redirect.objects.create(
            project=self.pip,
            redirect_type='exact',
            from_url='/en/oldversion/',
            to_url='/en/newversion/',
        )
        r = self.client.get('/en/oldversion/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/newversion/',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_keeps_version_number(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='page',
            from_url='/how_to_install.html', to_url='/install.html',
        )
        r = self.client.get(
            '/en/0.8.2/how_to_install.html',
            HTTP_HOST='pip.readthedocs.org',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.readthedocs.org/en/0.8.2/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_keeps_language(self):
        self.pip.language = 'de'
        self.pip.save()
        Redirect.objects.create(
            project=self.pip, redirect_type='page',
            from_url='/how_to_install.html', to_url='/install.html',
        )
        r = self.client.get(
            '/de/0.8.2/how_to_install.html',
            HTTP_HOST='pip.readthedocs.org',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.readthedocs.org/de/0.8.2/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_recognizes_custom_cname(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='page', from_url='/install.html',
            to_url='/tutorial/install.html',
        )
        r = self.client.get(
            '/install.html',
            HTTP_HOST='pip.pypa.io',
            HTTP_X_RTD_SLUG='pip',
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'],
            'http://pip.pypa.io/en/latest/tutorial/install.html',
        )

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_html(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_html',
        )
        r = self.client.get('/en/latest/faq/', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/faq.html',
        )

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_html_index(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_html',
        )
        r = self.client.get('/en/latest/faq/index.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/faq.html',
        )

    @override_settings(USE_SUBDOMAIN=True, PYTHON_MEDIA=True)
    def test_redirect_htmldir(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='sphinx_htmldir',
        )
        r = self.client.get('/en/latest/faq.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/faq/',
        )

    @override_settings(USE_SUBDOMAIN=True)
    def test_redirect_root_with_301_status(self):
        Redirect.objects.create(
            project=self.pip, redirect_type='prefix',
            from_url='/woot/', http_status=301,
        )
        r = self.client.get('/woot/faq.html', HTTP_HOST='pip.readthedocs.org')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r['Location'], 'http://pip.readthedocs.org/en/latest/faq.html',
        )


class CustomRedirectTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.pip = Project.objects.create(**{
            'repo_type': 'git',
            'name': 'Pip',
            'default_branch': '',
            'project_url': 'http://pip.rtfd.org',
            'repo': 'https://github.com/fail/sauce',
            'default_version': LATEST,
            'privacy_level': 'public',
            'version_privacy_level': 'public',
            'description': 'wat',
            'documentation_type': 'sphinx',
        })
        Redirect.objects.create(
            project=cls.pip,
            redirect_type='page',
            from_url='/install.html',
            to_url='/install.html#custom-fragment',
        )

    def test_redirect_fragment(self):
        redirect = Redirect.objects.get(project=self.pip)
        path = redirect.get_redirect_path('/install.html')
        expected_path = '/docs/pip/en/latest/install.html#custom-fragment'
        self.assertEqual(path, expected_path)


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class RedirectBuildTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.project = get(
            Project,
            slug='project-1',
            documentation_type='sphinx',
            conf_py_file='test_conf.py',
            versions=[fixture()],
        )
        self.version = self.project.versions.all()[0]

    def test_redirect_list(self):
        r = self.client.get('/builds/project-1/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], '/projects/project-1/builds/')

    def test_redirect_detail(self):
        r = self.client.get('/builds/project-1/1337/')
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r['Location'], '/projects/project-1/builds/1337/')


@override_settings(PUBLIC_DOMAIN='readthedocs.org', USE_SUBDOMAIN=False)
class GetFullPathTests(TestCase):
    fixtures = ['eric', 'test_data']

    def setUp(self):
        self.proj = Project.objects.get(slug='read-the-docs')
        self.redirect = get(Redirect, project=self.proj)

    def test_http_filenames_return_themselves(self):
        # If the crossdomain flag is False (default), then we don't redirect to a different host
        self.assertEqual(
            self.redirect.get_full_path('http://rtfd.org'),
            '/docs/read-the-docs/en/latest/http://rtfd.org',
        )

        self.assertEqual(
            self.redirect.get_full_path('http://rtfd.org', allow_crossdomain=True),
            'http://rtfd.org',
        )

    def test_redirects_no_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path('index.html'),
            '/docs/read-the-docs/en/latest/index.html',
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org',
    )
    def test_redirects_with_subdomain(self):
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/en/latest/faq.html',
        )

    @override_settings(
        USE_SUBDOMAIN=True, PRODUCTION_DOMAIN='rtfd.org',
    )
    def test_single_version_with_subdomain(self):
        self.redirect.project.single_version = True
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/faq.html',
        )

    def test_single_version_no_subdomain(self):
        self.redirect.project.single_version = True
        self.assertEqual(
            self.redirect.get_full_path('faq.html'),
            '/docs/read-the-docs/faq.html',
        )
