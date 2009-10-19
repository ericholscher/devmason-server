from django.core import urlresolvers
from django.shortcuts import get_object_or_404
from .models import Project
from .utils import BaseHandler, allow_404

class ProjectListHandler(BaseHandler):
    allowed_methods = ['GET']
    viewname = 'project_list'
    
    def read(self, request):
        return {
            'projects': Project.objects.all(),
            'links': self.build_links(request, ('self', ProjectListHandler))
        }

class ProjectHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Project
    viewname = 'project_detail'
    fields = ('name', 'slug', 'owner')
    
    @classmethod
    def owner(cls, project):
        if project.owner:
            return project.owner.username
        else:
            return ''
    
    @allow_404
    def read(self, request, slug):
        proj = get_object_or_404(Project, slug=slug)
        return {
            'name': proj.name,
            'slug': proj.slug,
            'owner': self.owner(proj),
            'links': self.build_links(request, 
                ('self', ProjectHandler, slug),
            )
        }

# def info_for_package(package):
#     ret_val = {}
#     for client in package.clients.all():
#        ret_val[client.host] = {'client': client,
#                               'results': client.results.all() }
#     return ret_val
# 
# class RootHandler(BaseHandler):
#     allowed_methods = ('GET',)
#     def read(self, request):
#         return Package.objects.all()
# 
# class PackageHandler(BaseHandler):
#     allowed_methods = ('GET', 'POST', 'DELETE')
#     model = Package
# 
#     def read(self, request, slug):
#        try:
#           package = Package.objects.get(slug=slug)
#           return info_for_package(package)
#        except:
#           last_10 = Package.objects.filter(slug__istartswith=slug)[:10]
#           return last_10
# 
#     @throttle(5, 10*60) # allow 5 times in 10 minutes
#     def create(self, request, slug):
#         package, created = Package.objects.get_or_create(slug=slug)
#         if created:
#             package.name = request.POST['name']
#             package.save()
#             return rc.CREATED
#         else:
#             return rc.FORBIDDEN.write('Package already exists')
# 
#     def delete(self, request, slug):
#         package = Package.objects.get(slug=slug)
#         package.delete()
#         return rc.DELETED # returns HTTP 204
# 
# 
# class BuildHandler(BaseHandler):
#     allowed_methods = ('GET', 'POST', 'DELETE')
#     model = Result
# 
#     def read(self, request, slug, data=None, latest=False):
#         if latest:
#             return {'latest_results': Result.objects.filter(client__package__slug=slug) }
#         if data:
#             return {'specific_results': Result.objects.get(pk=data) }
#         return {'results': Result.objects.filter(client__package__slug=slug) }
# 
#     def create(self, request, slug):
#         from pony_server.views import add_results
#         import simplejson
#         info = simplejson.loads(request.POST['info'])
#         results = simplejson.loads(request.POST['results'])
#         add_results(info, results)
#         return rc.CREATED
# 
# class TagHandler(BaseHandler):
#     allowed_methods = ('GET', 'POST', 'DELETE')
#     model = Tag
# 
#     def read(self, request, slug, data=None, latest=False):
#         if latest:
#             return {'latest_results': Result.objects.filter(client__tags__slug=data) }
#         if data:
#             return {'tag_results': Result.objects.filter(client__tags__slug=data) }
#         return {'all_tags': Tag.objects.filter(clients__package__slug=slug) }
