"""Rebuild documentation for all projects."""

from django.core.management.base import BaseCommand, CommandError

from readthedocs.builds.models import Build, Version
from readthedocs.projects.tasks import update_docs_task
from readthedocs.projects.models import Project


from readthedocs.docsitalia.models import Publisher, PublisherProject


class Command(BaseCommand):

    """Rebuild all projects command."""

    help = 'Rebuild projects'

    def add_arguments(self, parser):
        """adds arguments."""
        parser.add_argument(
            '--publisher', nargs='?', type=str,
            help='A publisher project slug'
        )
        parser.add_argument(
            '--document', nargs='?', type=str,
            help='A Read the docs document slug'
        )
        # argparse.ArgumentError: argument --version: conflicting option string: --version
        parser.add_argument(
            '--version_slug', nargs='?', type=str,
            help='A Read the docs version slug', required=True
        )
        parser.add_argument(
            '--async', action='store_true', default=False,
            help='Run the rebuild tasks async'
        )

    # pylint: disable=too-many-branches
    def handle(self, *args, **options):
        """handle command."""
        versions = Version.objects.all()
        publisher = options['publisher']
        version_slug = options['version_slug']
        print(version_slug)
        document = options['document']
        run_async = options['async']
        if publisher:
            try:
                projects = PublisherProject.objects.filter(
                    publisher=Publisher.objects.get(slug=publisher)
                ).values_list('projects', flat=True)
                versions = versions.filter(project__in=projects)
            except Publisher.DoesNotExist:
                raise CommandError("Publisher {} doesn't exist".format(publisher))
        if document:
            try:
                project = Project.objects.get(slug=document)
                versions = versions.filter(project=project)
            except Project.DoesNotExist:
                raise CommandError("Project {} doesn't exist".format(document))
        try:
            versions = versions.filter(slug=version_slug)
        except Project.DoesNotExist:
            raise CommandError("Project {} doesn't exist".format(document))
        for version in versions:
            task = update_docs_task
            build = Build.objects.create(
                project=version.project,
                version=version,
                type='html',
                state='triggered',
            )
            # corrected version
            # in new version of task we are not calling send_external_build_status
            # if 'commit' is not passed (do we need it?)
            # and we are not passing search=True (build_docs_search is no more building anything)
            kwargs = dict(
                version_pk=version.pk, build_pk=build.pk, project=version.project
            )
            if run_async:
                task.apply_async(kwargs=kwargs)
            else:
                task.run(**kwargs)

            # versions from update_repos
            # update_docs_task(
            #     version.project_id,
            #     build_pk=build.pk,
            #     version_pk=version.pk,
            # )

            # versions from update_repos
            # update_docs_task(
            #     version.pk,
            #     record=False,
            # )

            # versions from update_repos
            # update_docs_task(
            #     version.pk,
            #     build_pk=build.pk,
            # )
