import json
import time
import mock
import pytest
from django.urls import reverse
from django_dynamic_fixture import G

from readthedocs.builds.models import Version
from readthedocs.docsitalia.models import Publisher, PublisherProject
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.documents import PageDocument, ProjectDocument
from readthedocs.search.tasks import index_objects_to_es
from readthedocs.search.tests.utils import get_search_query_from_project_file


@pytest.mark.django_db
@pytest.mark.search
class TestSearch:
    fixtures = ['eric', 'test_data']

    def test_docsitalia_api_results_with_publisher(self, all_projects, client, es_index):

        publisher = Publisher.objects.create(
            name='Test Org',
            slug='publisher',
            metadata={},
            projects_metadata={},
            active=True
        )
        pub_project = PublisherProject.objects.create(
            name='Test Project',
            slug='testproject',
            metadata={
                'documents': [
                    'https://github.com/testorg/myrepourl',
                    'https://github.com/testorg/anotherrepourl',
                ]
            },
            publisher=publisher,
            active=True
        )
        project = all_projects[0]
        pub_project.projects.add(project)

        kwargs = {
            'app_label': Project._meta.app_label,
            'model_name': Project.__name__,
            'document_class': str(ProjectDocument),
            'objects_id': [project.id],
        }

        index_objects_to_es.delay(**kwargs)
        inst = ProjectDocument.get(id=project.id)

        assert inst.publisher == publisher.name
        assert inst.publisher_project == pub_project.slug

    @mock.patch('readthedocs.search.api.PageSearch')
    def test_docsitalia_api_empty_results(self, execute, all_projects, client, es_index):
        execute.return_value = []
        project = all_projects[0]
        query = get_search_query_from_project_file(project_slug=project.slug)
        url = reverse('doc_search')
        search_params = {'q': query, 'project': project.slug, 'version': 'latest'}

        response = client.get(url, search_params)
        assert response.status_code == 200
        expected = {"count": 0, "next": None, "previous": None, "results": []}
        assert json.loads(response.content.decode('utf-8')) == expected


@pytest.mark.django_db
@pytest.mark.search
class TestDocsItaliaPageSearch(object):
    url = reverse('search')

    def _get_search_result(self, url, client, search_params):
        resp = client.get(url, search_params)
        assert resp.status_code == 200

        results = resp.context['results']
        facets = resp.context['facets']

        return results, facets

    def test_search_filter_default_version(self, client, all_projects):
        search_params = {'q': 'celery', 'type': 'file'}
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params
        )
        assert len(results) == 5

        for result in results:
            project = Project.objects.get(slug=result.project)
            assert result.version == project.default_version
            assert result.is_default

        search_params['version'] = 'latest'

        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params
        )

        assert len(results) == 5

        project = all_projects[0]
        new_version = G(Version, project=project)
        html_files = HTMLFile.objects.filter(project=project)
        # create HTML files for different version
        for html_file in html_files:
            new_html = G(HTMLFile, project=project, version=new_version, name=html_file.name)
            PageDocument().update(new_html)

        query = get_search_query_from_project_file(project_slug=project.slug)
        search_params = {'q': query, 'type': 'file'}
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 1
        assert results[0].is_default
        assert project.default_version == results[0].version

        search_params['version'] = new_version.slug
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 1

        assert search_params['version'] == results[0].version
        assert not results[0].is_default

        search_params['version'] = 'nonexistent'
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert not results

    @pytest.mark.skip(reason="doesn't work with CELERY_ALWAYS_EAGER=True")
    def test_change_default_version(self, client, all_projects, settings):
        project = all_projects[0]
        new_version = G(Version, project=project)
        html_files = HTMLFile.objects.filter(project=project)
        for html_file in html_files:
            new_html = G(HTMLFile, project=project, version=new_version, name=html_file.name)
            PageDocument().update(new_html)

        query = get_search_query_from_project_file(project_slug=project.slug)
        search_params = {'q': query, 'type': 'file'}
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 1
        assert results[0].is_default
        assert project.default_version == results[0].version
        assert new_version.slug != results[0].version

        project.default_version = new_version.slug
        project.save()
        time.sleep(2)
        results, facets = self._get_search_result(
            url=self.url,
            client=client,
            search_params=search_params,
        )
        assert len(results) == 1
        assert results[0].is_default
        assert project.default_version == results[0].version
        assert new_version.slug == results[0].version
