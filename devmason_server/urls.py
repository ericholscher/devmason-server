from django.conf.urls.defaults import *
from .utils import Resource
from . import handlers

urlpatterns = patterns('',
    url(r'^$',
        Resource(handlers.ProjectListHandler),
        name = 'project_list'
    ),
    url(r'builds/github',
        'devmason_server.views.github_build',
        name='github_build'
    ),
    url(r'builds/bitbucket',
        'devmason_server.views.bitbucket_build',
        name='bitbucket_build'
    ),
    url(r'builds/request',
        'devmason_server.views.request_build',
        name='request_build'
    ),
    url(r'add_project',
        'devmason_server.views.add_project',
        name='project_add'
    ),
    url(r'xmlrpc',
        'devmason_server.views.xmlrpc',
        name='xmlrpc'
    ),
    url(r'^(?P<slug>[\w-]+)$',
        Resource(handlers.ProjectHandler),
        name = 'project_detail'
    ),
    url(r'^(?P<slug>[\w-]+)/claim$',
        'devmason_server.views.claim_project',
        name = 'claim_project'
    ),
    url(r'^(?P<slug>[\w-]+)/builds$',
        Resource(handlers.ProjectBuildListHandler),
        name = 'project_build_list'
    ),
    url(r'^(?P<slug>[\w-]+)/builds/(?P<build_id>\d+)$',
        Resource(handlers.BuildHandler),
        name = 'build_detail'
    ),
    url(r'^(?P<slug>[\w-]+)/builds/latest$',
        Resource(handlers.LatestBuildHandler),
        name = 'latest_build'
    ),
    url(r'^(?P<slug>[\w-]+)/tags$',
        Resource(handlers.ProjectTagListHandler),
        name = 'project_tag_list'
    ),
    url(r'^(?P<slug>[\w-]+)/tags/(?P<tags>[^/]+)/latest$',
        Resource(handlers.ProjectLatestTaggedBuildHandler),
        name = 'latest_tagged_build'
    ),
    url(r'^(?P<slug>[\w-]+)/tags/(?P<tags>.*)$',
        Resource(handlers.TagHandler),
        name = 'tag_detail'
    ),
)
