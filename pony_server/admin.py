from django.contrib import admin
from pony_server.models import Result, Client


admin.site.register(Client)
admin.site.register(Result)

