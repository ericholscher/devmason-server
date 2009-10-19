from django.conf.urls.defaults import *
from .utils import Resource
from .handlers import ProjectListHandler, ProjectHandler

urlpatterns = patterns('',
   url(r'^$',                   Resource(ProjectListHandler),   name='project_list'),
   url(r'^(?P<slug>[\w-]+)$',   Resource(ProjectHandler),       name='project_detail'),
)
