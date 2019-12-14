import json
from pprint import pprint

import mock
import pytest
from django.conf import settings
from django.urls import reverse
from django_elasticsearch_dsl import Index

from readthedocs.docsitalia.models import Publisher, PublisherProject
from readthedocs.projects.models import Project
from readthedocs.search.documents import ProjectDocument
from readthedocs.search.tasks import index_objects_to_es
from readthedocs.search.tests.utils import get_search_query_from_project_file, DATA_TYPES_VALUES



@pytest.mark.django_db
@pytest.mark.search
class TestDocsItaliaSearch:
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

    def test_search_file_priority(self, client, all_projects):
        by_slug = {}
        for index, project in enumerate(all_projects):
            by_slug[project.slug] = project
            project.projectorder.priority = 100 - index
            project.projectorder.save()

        results, _ = self._get_search_result(
            url=self.url,
            client=client,
            search_params={ 'q': '*', 'type': 'file' }
        )
        assert len(results) >= 1

        previous_priority = 100
        # enumerating all the index content and checking that priority are strictly in decreasing order
        # and project and index has the same priority for the same project
        for index, result in enumerate(results):
            project_by_slug = by_slug[result.project]
            assert previous_priority >= result.priority
            assert result.priority == project_by_slug.projectorder.priority
            previous_priority = result.priority
