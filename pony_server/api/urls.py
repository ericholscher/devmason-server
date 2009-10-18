from django.conf.urls.defaults import *
from piston.resource import Resource
from pony_server.api.handlers import PackageHandler, RootHandler, BuildHandler, TagHandler

package_handler = Resource(PackageHandler)
root_handler = Resource(RootHandler)
build_handler = Resource(BuildHandler)
tag_handler = Resource(TagHandler)

urlpatterns = patterns('',
   url(r'^package/(?P<slug>[^/]+)/builds/latest/', build_handler, {'latest': True }),
   url(r'^package/(?P<slug>[^/]+)/builds/(?P<data>[^/]+)/', build_handler),
   url(r'^package/(?P<slug>[^/]+)/builds/', build_handler),

   url(r'^package/(?P<slug>[^/]+)/tags/(?P<data>[^/]+)/latest/', tag_handler, {'latest': True }),
   url(r'^package/(?P<slug>[^/]+)/tags/(?P<data>[^/]+)/', tag_handler),
   url(r'^package/(?P<slug>[^/]+)/tags/', tag_handler),

   url(r'^package/(?P<slug>[^/]+)/', package_handler),
   url(r'^$', root_handler),
)
