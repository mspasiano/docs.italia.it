import logging

from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields

from elasticsearch import Elasticsearch

from readthedocs.docsitalia.models import Publisher, PublisherProject
from readthedocs.projects.models import HTMLFile, Project


project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])

log = logging.getLogger(__name__)


class RTDDocTypeMixin:

    def update(self, *args, **kwargs):
        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic indexing to fix connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
        super().update(*args, **kwargs)


@project_index.doc_type
class ProjectDocument(RTDDocTypeMixin, DocType):

    # Metadata
    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(
        properties={
            'username': fields.TextField(),
            'id': fields.IntegerField(),
        }
    )
    language = fields.KeywordField()

    modified_model_field = 'modified_date'

    # DocsItalia
    docsitalia = fields.ObjectField(
        properties={
            'project': fields.KeywordField(),
            'publisher': fields.TextField(),
        }
    )

    class Meta:
        model = Project
        fields = ('name', 'slug', 'description')
        ignore_signals = True
        # Ensure the Project is reindexed when Publisher or PublisherProject is updated
        related_models = [PublisherProject, Publisher]

    def get_queryset(self):
        """Fetch related instances."""
        return super().get_queryset().prefetch_related(
            'publisherproject_set__publisher'
        )

    def get_instances_from_related(self, related_instance):
        """If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, Publisher):
            return Project.objects.filter(publisherproject__publisher=related_instance)
        elif isinstance(related_instance, PublisherProject):
            return related_instance.projects.all()

    def prepare_docsitalia(self, instance):
        """Return docsitalia object."""
        # not using more sophisticated Django methods in order to exploit prefetching
        publisher_projects = list(instance.publisherproject_set.all())
        if publisher_projects:
            return {
                'project': publisher_projects[0].slug,
                'publisher': publisher_projects[0].publisher.name
            }


    @classmethod
    def faceted_search(cls, query, user, language=None):
        from readthedocs.search.faceted_search import ProjectSearch
        kwargs = {
            'user': user,
            'query': query,
        }

        if language:
            kwargs['filters'] = {'language': language}

        return ProjectSearch(**kwargs)


@page_index.doc_type
class PageDocument(RTDDocTypeMixin, DocType):

    # Metadata
    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')
    path = fields.KeywordField(attr='processed_json.path')
    full_path = fields.KeywordField(attr='path')

    # Searchable content
    title = fields.TextField(attr='processed_json.title')
    sections = fields.NestedField(
        attr='processed_json.sections',
        properties={
            'id': fields.KeywordField(),
            'title': fields.TextField(),
            'content': fields.TextField(),
        }
    )
    domains = fields.NestedField(
        properties={
            'role_name': fields.KeywordField(),

            # For linking to the URL
            'anchor': fields.KeywordField(),

            # For showing in the search result
            'type_display': fields.TextField(),
            'docstrings': fields.TextField(),

            # Simple analyzer breaks on `.`,
            # otherwise search results are too strict for this use case
            'name': fields.TextField(analyzer='simple'),
        }
    )

    modified_model_field = 'modified_date'

    class Meta:
        model = HTMLFile
        fields = ('commit', 'build')
        ignore_signals = True

    def prepare_domains(self, html_file):
        """Prepares and returns the values for domains field."""
        all_domains = []

        try:
            domains_qs = html_file.sphinx_domains.exclude(
                domain='std',
                type__in=['doc', 'label']
            ).iterator()

            all_domains = [
                {
                    'role_name': domain.role_name,
                    'anchor': domain.anchor,
                    'type_display': domain.type_display,
                    'docstrings': html_file.processed_json.get(
                        'domain_data', {}
                    ).get(domain.anchor, ''),
                    'name': domain.name,
                }
                for domain in domains_qs
            ]

            log.debug("[%s] [%s] Total domains for file %s are: %s" % (
                html_file.project.slug,
                html_file.version.slug,
                html_file.path,
                len(all_domains),
            ))

        except Exception:
            log.exception("[%s] [%s] Error preparing domain data for file %s" % (
                html_file.project.slug,
                html_file.version.slug,
                html_file.path,
            ))

        return all_domains

    @classmethod
    def faceted_search(
            cls, query, user, projects_list=None, versions_list=None,
            filter_by_user=True
    ):
        from readthedocs.search.faceted_search import PageSearch
        kwargs = {
            'user': user,
            'query': query,
            'filter_by_user': filter_by_user,
        }

        filters = {}
        if projects_list is not None:
            filters['project'] = projects_list
        if versions_list is not None:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return PageSearch(**kwargs)

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index."""
        queryset = super().get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.internal().filter(
            project__documentation_type__contains='sphinx'
        )

        # TODO: Make this smarter
        # This was causing issues excluding some valid user documentation pages
        # excluded_files = [
        #     'search.html',
        #     'genindex.html',
        #     'py-modindex.html',
        #     'search/index.html',
        #     'genindex/index.html',
        #     'py-modindex/index.html',
        # ]
        # for ending in excluded_files:
        #     queryset = queryset.exclude(path=ending)

        return queryset
