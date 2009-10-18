from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    url(r'^$', 'pony_server.views.index', name='index'),
    url(r'xmlrpc', 'pony_server.views.xmlrpc', name='xmlrpc'),
    (r'^api/', include('pony_server.api.urls')),
)
