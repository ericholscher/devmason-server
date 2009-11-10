from django.contrib import admin
from pony_server.models import Project, Build, BuildStep, BuildRequest, Repository

admin.site.register(Project)
admin.site.register(Build)
admin.site.register(BuildStep)
admin.site.register(Repository)
admin.site.register(BuildRequest)
