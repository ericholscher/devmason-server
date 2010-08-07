from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', include('devmason_server.urls')),
    (r'devmason/', include('devmason_server.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/(.*)', admin.site.root, name='admin-root'),

)
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
    )


