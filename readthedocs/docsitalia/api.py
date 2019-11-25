from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.faceted_search import PageSearch


class SearchSerializer(serializers.Serializer):
    title = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlight = serializers.SerializerMethodField()

    def get_link(self, obj):
        try:
            return self.context['projects_url'][obj.project] + obj.path
        except (AttributeError, KeyError, TypeError):
            return ""

    def get_highlight(self, obj):
        try:
            return obj.meta.highlight.title[0]
        except (AttributeError, IndexError):
            return ""


class SearchAPIView(generics.ListAPIView):
    """Main entry point to perform a search using Elasticsearch."""

    serializer_class = SearchSerializer

    def get_queryset(self):
        """
        Return Elasticsearch DSL Search object instead of Django Queryset.

        Django Queryset and elasticsearch-dsl ``Search`` object is similar pattern.
        So for searching, its possible to return ``Search`` object instead of queryset.
        The ``filter_backends`` and ``pagination_class`` is compatible with ``Search``
        """
        # Validate all the required params are there
        self.validate_query_params()
        query = self.request.query_params.get('q', '')
        kwargs = {'filter_by_user': False, 'filters': {}}
        kwargs['filters']['version'] = self.request.query_params.get('version', LATEST)
        user = self.request.user
        return PageSearch(query=query, user=user, **kwargs)

    def validate_query_params(self):
        """
        Validate all required query params are passed on the request.

        Query params required is: ``q``.

        :rtype: None

        :raises: ValidationError if one of them is missing.
        """
        try:
            self.request.query_params['q']
        except KeyError:
            raise ValidationError({'q': ["This query param is required"]})

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['projects_url'] = self.get_all_projects_url()
        return context

    def get_all_projects(self):
        """
        Return a list containing all projects.

        :rtype: list

        :raises: Http404 if project is not found
        """
        version_slug = self.request.query_params.get('version', LATEST)
        project_list = []
        for project in Project.objects.all():
            version = Version.internal.public(self.request.user).filter(
                project__slug=project.slug, slug=version_slug
            )
            if version.exists():
                project_list.append(version.first().project)
        return project_list

    def get_all_projects_url(self):
        """
        Return a dict containing the project slug and its version URL.

        The dictionary contains all projects. Each project's
        slug is used as a key and the documentation URL for that project and
        version as the value.

        Example:

        {
            "requests": "https://requests.readthedocs.io/en/latest/",
            "requests-oauth": "https://requests-oauth.readthedocs.io/en/latest/",
        }

        :rtype: dict
        """
        all_projects = self.get_all_projects()
        version_slug = self.request.query_params.get('version', LATEST)
        projects_url = {}
        for project in all_projects:
            projects_url[project.slug] = project.get_docs_url(version_slug=version_slug)
        return projects_url
