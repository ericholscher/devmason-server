from django.contrib import admin
from pony_server.models import Project, Build, BuildStep, BuildRequest, Repository

class BuildAdmin(admin.ModelAdmin):
    model = Build
    list_display = ('project', 'success', 'user', 'started')
    

admin.site.register(Project)
admin.site.register(Build, BuildAdmin)
admin.site.register(BuildStep)
admin.site.register(Repository)
admin.site.register(BuildRequest)
