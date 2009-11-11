from django.db import transaction
from django.core.paginator import Paginator, InvalidPage
from django.core import urlresolvers
from django.http import Http404, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import simplejson
from piston.handler import BaseHandler
from piston.utils import require_mime
from tagging.models import Tag
from .models import Project, Build, BuildStep
from .utils import (link, allow_404, authentication_required,
                    authentication_optional, format_dt, HttpResponseCreated,
                    HttpResponseNoContent, mk_datetime)

class ProjectListHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'project_list'

    def read(self, request):
        projects =  Project.objects.filter(builds__isnull=False)
        builds = {}
        for project in projects:
            builds[project.slug] = list(project.builds.all())[-1]
        return {
            'projects': projects,
            'builds': builds,
            'links': [link('self', ProjectListHandler)]
        }

class ProjectHandler(BaseHandler):
    allowed_methods = ['GET', 'PUT', 'DELETE']
    model = Project
    viewname = 'project_detail'
    fields = ('name', 'owner', 'links')

    @allow_404
    def read(self, request, slug):
        return  get_object_or_404(Project, slug=slug)

    @require_mime('json')
    @authentication_required
    def update(self, request, slug):
        # Check the one required field in the PUT data -- a name
        try:
            project_name = request.data['name']
        except (TypeError, KeyError):
            return HttpResponseBadRequest()

        # If there's an existing project, the updating user has to match the
        # user who created the project
        try:
            project = Project.objects.get(slug=slug)
        except Project.DoesNotExist:
            # The project doesn't exist, so save the user if it's a
            # new one, create the project, then return 201 created
            if request.user.is_new_user:
                request.user.save()
            project = Project.objects.create(name=project_name, slug=slug, owner=request.user)
            return HttpResponseCreated(urlresolvers.reverse(self.viewname, args=[slug]))

        # Okay, so if we fall through to here then we're trying to update an
        # existing project. This means checking that the user's allowed to
        # do so before updating it.
        if request.user.is_new_user or project.owner != request.user:
            return HttpResponseForbidden()

        # Hey, look, we get to update this project.
        project.name = project_name
        project.save()

        # PUT returns the newly updated representation
        return self.read(request, slug)

    @allow_404
    @authentication_required
    def delete(self, request, slug):
        project = get_object_or_404(Project, slug=slug)

        # New users don't get to delete packages; neither do non-owners
        if request.user.is_new_user or project.owner != request.user:
            return HttpResponseForbidden()

        # Otherwise delete it.
        project.delete()
        return HttpResponseNoContent()

    @classmethod
    def owner(cls, project):
        if project.owner:
            return project.owner.username
        else:
            return ''

    @classmethod
    def links(cls, project):
        return [
            link('self', ProjectHandler, project.slug),
            link('build-list', ProjectBuildListHandler, project.slug),
            link('latest-build', LatestBuildHandler, project.slug),
            link('tag-list', ProjectTagListHandler, project.slug),
        ]

class PaginatedBuildHandler(BaseHandler):
    """Helper base class to provide paginated builds"""

    def handle_paginated_builds(self, builds, qdict, link_callback, extra={}):
        try:
            per_page = int(qdict['per_page'])
        except (ValueError, KeyError):
            per_page = 25

        paginator = Paginator(builds, per_page)

        try:
            page = paginator.page(qdict['page'])
        except (KeyError, InvalidPage):
            page = paginator.page(1)

        if not page.object_list:
            raise Http404("No builds")

        link_callback('self', page=page.number, per_page=per_page)

        if page.has_other_pages():
            link_callback('first', page=1, per_page=per_page)
            link_callback('last', page=paginator.num_pages, per_page=per_page)
            if page.has_previous():
                link_callback('previous', page=page.previous_page_number(), per_page=per_page)
            if page.has_next():
                link_callback('next', page=page.next_page_number(), per_page=per_page)

        response = {
            'builds': page.object_list,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'page': page.number,
            'paginated': page.has_other_pages(),
            'per_page': per_page,
        }
        return dict(response, **extra)

class ProjectBuildListHandler(PaginatedBuildHandler):
    allowed_methods = ['GET', 'POST']
    viewname = 'project_build_list'

    @allow_404
    def read(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        builds = project.builds.all()

        links = [
            link('project', ProjectHandler, project.slug),
            link('latest-build', LatestBuildHandler, project.slug),
        ]

        def make_link(rel, **kwargs):
            # None of the paginated pages should allow anything other than GET
            l = link(rel, self, project.slug, **kwargs)
            l['allowed_methods'] = ['GET']
            links.append(l)

        response = self.handle_paginated_builds(builds, request.GET, make_link)
        response['links'] = links
        response['project'] = project
        return response

    @allow_404
    @require_mime('json')
    @authentication_optional
    @transaction.commit_on_success
    def create(self, request, slug):
        project = get_object_or_404(Project, slug=slug)

        # Construct us the dict of "extra" info from the request
        data = request.data
        extra = request.data['client'].copy()
        for k in ('success', 'started', 'finished', 'client', 'results', 'tags'):
            extra.pop(k, None)

        # Create the Build object
        try:
            build = Build.objects.create(
                project = project,
                success = data['success'],
                started = mk_datetime(getattr(data, 'started', '')),
                finished = mk_datetime(getattr(data, 'finished', '')),
                host = data['client']['host'],
                arch = data['client']['arch'],
                user = request.user.is_authenticated() and request.user or None,

                # Because of some weirdness with the way fields are handled in
                # __init__, we have to encode extra as JSON manually here.
                # TODO: investiage why and fix JSONField
                extra_info = simplejson.dumps(extra),
            )
        except (KeyError, ValueError), ex:
            # We'll get a KeyError from request.data[k] if the given key
            # is missing and ValueError from improperly formatted dates.
            # Treat either of these as improperly formatted requests
            # and return a 400 (Bad Request)
            return HttpResponseBadRequest(str(ex))

        # Tag us a build
        if 'tags' in data:
            build.tags = ",".join(data['tags'])

        # Create each build step
        for result in request.data.get('results', []):
            # extra_info logic as above
            extra = result.copy()
            for k in ('success', 'started', 'finished', 'name', 'output', 'errout'):
                extra.pop(k, None)

            # Create the BuildStep, handling errors as above
            try:
                BuildStep.objects.create(
                    build = build,
                    success = result['success'],
                    started = mk_datetime(getattr(result, 'started', '')),
                    finished = mk_datetime(getattr(result, 'finished', '')),
                    name = result['name'],
                    output = result.get('output', ''),
                    errout = result.get('errout', ''),
                    extra_info = simplejson.dumps(extra),
                )
            except (KeyError, ValueError), ex:
                # We'll get a KeyError from request.data[k] if the given key
                # is missing and ValueError from improperly formatted dates.
                # Treat either of these as improperly formatted requests
                # and return a 400 (Bad Request)
                return HttpResponseBadRequest(str(ex))

        # It worked! Return a 201 created
        url = urlresolvers.reverse(BuildHandler.viewname, args=[project.slug, build.pk])
        return HttpResponseCreated(url)

class BuildHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Build
    fields = ('success', 'started', 'finished', 'tags',
              'client', 'results', 'links')
    viewname = 'build_detail'

    @allow_404
    def read(self, request, slug, build_id):
        return get_object_or_404(Build, project__slug=slug, pk=build_id)

    @classmethod
    def tags(cls, build):
        return [t.name for t in build.tags]

    @classmethod
    def started(cls, build):
        return format_dt(build.started)

    @classmethod
    def finished(cls, build):
        return format_dt(build.finished)

    @classmethod
    def client(cls, build):
        details = {
            'host': build.host,
            'user': build.user and build.user.username or '',
            'arch': build.arch,
        }
        if build.extra_info != '""':
            details.update(build.extra_info)
        return details

    @classmethod
    def results(cls, build):
        rv = []
        for step in build.steps.all():
            step_data = {
                'success': step.success,
                'started': format_dt(step.started),
                'finished': format_dt(step.finished),
                'name': step.name,
                'output': step.output,
                'errout': step.errout,
            }
            step_data.update(step.extra_info)
            rv.append(step_data)
        return rv

    @classmethod
    def links(cls, build):
        links = [
            link('self', BuildHandler, build.project.slug, build.pk),
            link('project', ProjectHandler, build.project.slug),
        ]
        for tag in build.tags:
            links.append(link('tag', TagHandler, build.project.slug, tag.name))
        return links

class LatestBuildHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'latest_build'

    @allow_404
    def read(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        build = project.builds.latest('finished')
        return redirect('build_detail', slug, build.pk)

class ProjectTagListHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'project_tag_list'

    @allow_404
    def read(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        tags = Tag.objects.usage_for_model(Build, filters={'project': project})

        links = [
            link('self', ProjectTagListHandler, project.slug),
            link('project', ProjectHandler, project.slug),
        ]
        links.extend(link('tag', TagHandler, project.slug, tag.name) for tag in tags)

        return {
            'tags': [tag.name for tag in tags],
            'links': links,
        }

class TagHandler(PaginatedBuildHandler):
    allowed_methods = ['GET']
    viewname = 'tag_detail'
    model = Tag

    @allow_404
    def read(self, request, slug, tags):
        project = get_object_or_404(Project, slug=slug)
        tag_list = tags.split(';')
        builds = Build.tagged.with_all(tags, queryset=project.builds.all())

        links = []
        def make_link(rel, **kwargs):
            links.append(link(rel, self, project.slug, tags, **kwargs))

        response = self.handle_paginated_builds(builds, request.GET, make_link, {'tags': tag_list})
        response['links'] = links
        return response

class ProjectLatestTaggedBuildHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'latest_tagged_build'

    @allow_404
    def read(self, request, slug, tags):
        project = get_object_or_404(Project, slug=slug)
        tag_list = tags.split(';')
        builds = Build.tagged.with_all(tags, queryset=project.builds.all())
        try:
            b = builds[0]
        except IndexError:
            raise Http404("No builds")
        return redirect('build_detail', project.slug, b.pk)
