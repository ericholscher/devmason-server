from django.contrib import admin
from pony_server.models import Result, Client, Package, Tag


admin.site.register(Client)
admin.site.register(Result)
admin.site.register(Package)
admin.site.register(Tag)
