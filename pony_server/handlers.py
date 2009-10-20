from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import get_object_or_404
from piston.handler import BaseHandler
from .models import Project, Build, BuildStep
from .utils import link, allow_404, format_dt

class ProjectListHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'project_list'
    
    def read(self, request):
        return {
            'projects': Project.objects.all(),
            'links': [link('self', ProjectListHandler)]
        }

class ProjectHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Project
    viewname = 'project_detail'
    fields = ('name', 'slug', 'owner', 'links')
    
    @allow_404
    def read(self, request, slug):
        return get_object_or_404(Project, slug=slug)
    
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
            # link('latest-build', ProjectLatestBuildHandler, project.slug),
            # link('tag-list', ProjectTagListHandler, project.slug),
        ]
        
class ProjectBuildListHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'project_build_list'
    
    @allow_404
    def read(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        builds = project.builds.all()
        
        try:
            per_page = int(request.GET['per_page'])
        except (ValueError, KeyError):
            per_page = 25
        
        paginator = Paginator(builds, per_page)
        
        try:
            page = paginator.page(request.GET['page'])
        except (KeyError, InvalidPage):
            page = paginator.page(1)
                    
        links = [
           link('self', ProjectBuildListHandler, project.slug, 
                page=page.number, per_page=per_page),
           link('project', ProjectHandler, project.slug)
           # link('latest-build', ProjectLatestBuildHandler, project.slug),
        ]
        if page.has_other_pages():
            links.extend([
                link('first', ProjectBuildListHandler, project.slug, 
                     page=1, per_page=per_page),
                link('last', ProjectBuildListHandler, project.slug, 
                     page=paginator.num_pages, per_page=per_page),
            ])
            if page.has_previous_page():
                links.append(
                    link('previous', ProjectBuildListHandler, project.slug, 
                         page=page.previous_page_number(), per_page=per_page))
            if page.has_next_page():
                links.append(
                    link('next', ProjectBuildListHandler, project.slug,
                         page=page.next_page_number(), per_page=per_page))
        
        return {
            'builds': page.object_list,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'page': page.number,
            'paginated': page.has_other_pages(),
            'per_page': per_page,
            'links': links,
        }

class BuildHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Build
    fields = ('success', 'started', 'finished', 'tags',
              'client', 'results', 'links')
    viewname = 'build_detail'
    
    @allow_404
    def read(self, request, project_slug, build_id):
        return get_object_or_404(Build, project__slug=project_slug, pk=build_id)
        
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
        # for tag in build.tags:
        #     links.append(link('tag', TagHandler, build.project.slug, tag.name))
        return links