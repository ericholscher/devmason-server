from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    (r'^api/', include('pony_server.api.urls')),
    url(r'^(?P<slug>[^/]+)/(?P<id>\d+)/', 'pony_server.views.result_detail', name='result_detail'),
    url(r'^(?P<slug>[^/]+)/', 'pony_server.views.package_list', name='package_list'),
    url(r'xmlrpc', 'pony_server.views.xmlrpc', name='xmlrpc'),
    url(r'^$', 'pony_server.views.index', name='index'),
)
