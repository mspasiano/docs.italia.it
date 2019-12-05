from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch_dsl import analyzer, tokenizer

from readthedocs.docsitalia.models import Publisher
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import HTMLFile, Project
from readthedocs.search.documents import RTDDocTypeMixin

trigram_analyzer = analyzer(
    'trigram_analyzer',
    tokenizer=tokenizer('trigram', 'nGram', min_gram=3, max_gram=3),
    filter=['lowercase']
)

quicksearch_conf = settings.ES_INDEXES['quicksearch']
quicksearch_index = Index(quicksearch_conf['name'])
quicksearch_index.settings(**quicksearch_conf['settings'])


@quicksearch_index.doc_type
class PageQuickSearchDocument(RTDDocTypeMixin, DocType):

    model = fields.KeywordField()
    link = fields.KeywordField(attr='get_absolute_url')
    text = fields.TextField(attr='processed_json.title', analyzer=trigram_analyzer)
    version = fields.KeywordField(attr='version.slug')

    class Meta:
        model = HTMLFile
        ignore_signals = True

    def get_queryset(self):
        """
        Overwrite default queryset to filter certain files to index.

        Do not index files that belong to non sphinx project.
        Also do not index certain files.
        """
        return super().get_queryset().internal().select_related(
            'version',
        ).filter(
            project__documentation_type__contains='sphinx',
        ).exclude(version__privacy_level=PRIVATE)

    def prepare_model(self, obj):
        """Return the document model name."""
        return "page"


@quicksearch_index.doc_type
class ProjectQuickSearchDocument(RTDDocTypeMixin, DocType):

    model = fields.KeywordField()
    link = fields.KeywordField(attr='get_absolute_url')
    text = fields.TextField(attr='name', analyzer=trigram_analyzer)

    class Meta:
        model = Project
        ignore_signals = True

    def prepare_model(self, obj):
        """Return the document model name."""
        return "project"


@quicksearch_index.doc_type
class PublisherQuickSearchDocument(RTDDocTypeMixin, DocType):

    model = fields.KeywordField()
    link = fields.KeywordField(attr='get_absolute_url')
    text = fields.TextField(attr='name', analyzer=trigram_analyzer)

    class Meta:
        model = Publisher
        ignore_signals = True

    def prepare_model(self, obj):
        """Return the document model name."""
        return "publisher"
