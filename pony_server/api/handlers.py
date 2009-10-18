from piston.handler import BaseHandler
from pony_server.models import Package, Client, Result, Tag
from piston.utils import rc, throttle

def info_for_package(package):
    ret_val = {}
    for client in package.clients.all():
       ret_val[client.host] = {'client': client,
                              'results': client.results.all() }
    return ret_val

class RootHandler(BaseHandler):
    allowed_methods = ('GET',)
    def read(self, request):
        return Package.objects.all()

class PackageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = Package

    def read(self, request, slug):
       try:
          package = Package.objects.get(slug=slug)
          return info_for_package(package)
       except:
          last_10 = Package.objects.filter(slug__istartswith=slug)[:10]
          return last_10

    @throttle(5, 10*60) # allow 5 times in 10 minutes
    def create(self, request, slug):
        package, created = Package.objects.get_or_create(slug=slug)
        if created:
            package.name = request.POST['name']
            package.save()
            return rc.CREATED
        else:
            return rc.FORBIDDEN.write('Package already exists')

    def delete(self, request, slug):
        package = Package.objects.get(slug=slug)
        package.delete()
        return rc.DELETED # returns HTTP 204


class BuildHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = Result

    def read(self, request, slug, data=None, latest=False):
        if latest:
            return {'latest_results': Result.objects.filter(client__package__slug=slug) }
        if data:
            return {'specific_results': Result.objects.get(pk=data) }
        return {'results': Result.objects.filter(client__package__slug=slug) }

class TagHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = Tag

    def read(self, request, slug, data=None, latest=False):
        if latest:
            return {'latest_results': Result.objects.filter(client__tags__slug=data) }
        if data:
            return {'tag_results': Result.objects.filter(client__tags__slug=data) }
        return {'all_tags': Tag.objects.filter(clients__package__slug=slug) }
