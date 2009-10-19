from django.contrib import admin
from pony_server.models import Project, Build, BuildStep

admin.site.register(Project)
admin.site.register(Build)
admin.site.register(BuildStep)