try:
    import json
except:
    import simplejson as json
   
import datetime
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

from pony_server.models import Repository, BuildRequest, Project
from pony_server.handlers import ProjectBuildListHandler
from pony_server.utils import RequestFactory

def start_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    git_url = url.replace('http://', 'git://')
    hash = obj['after']

    project = Project.objects.get(slug=name)
    repo, created = Repository.objects.get_or_create(
         url=git_url,
         project=project,
         type='git',
    )
    brequest = BuildRequest.objects.create(
        repository = repo,
        identifier = hash,
        requested = datetime.datetime.utcnow(),
    )


# Create a Dispatcher; this handles the calls and translates info to function maps
dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None) # Python 2.5

def xmlrpc(request):
    response = HttpResponse()
    if len(request.POST):
        response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
    else:
        response.write("<b>This is an XML-RPC Service.</b><br>")
        response.write("You need to invoke it using an XML-RPC Client!<br>")
        response.write("The following methods are available:<ul>")
        methods = dispatcher.system_listMethods()

        for method in methods:
                sig = dispatcher.system_methodSignature(method)
                help = dispatcher.system_methodHelp(method)
                response.write("<li><b>%s</b>: [%s] %s" % (method, sig, help))
        response.write("</ul>")
        response.write('<a href="http://www.djangoproject.com/"> <img src="http://media.djangoproject.com/img/badges/djangomade124x25_grey.gif" border="0" alt="Made with Django." title="Made with Django."></a>')
    response['Content-length'] = str(len(response.content))
    return response



def add_results(info, results):
    "Return sweet results"
    build_dict = {'success': info.get('success', False),
                    #'started': ,
                    #'finished': ,
                    'tags': info['tags'],
                    'client': {
                        'arch': info.get('arch', ''),
                        'host':info.get('host', ''),
                        'user': 'pony-client',
                            },
                    'results': []
                }

    for result in results:
        build_dict['results'].append(
                       {'success': result.get('status', False),
                        'name': result.get('name', ''),
                        'errout': result.get('errout', ''),
                        'output': result.get('out', ''),
                        'command': result.get('command', ''),
                        'type': result.get('type', ''),
                        'version_type': result.get('version_type', ''),
                        'version_info': result.get('version_info', ''),
                       }
        )

    environ = {
        'PATH_INFO': '/',
        'QUERY_STRING': '',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'SERVER_NAME': 'testserver',
        'SERVER_PORT': 80,
        'SERVER_PROTOCOL': 'HTTP/1.1',
    }
    r = WSGIRequest(environ)
    r.data = build_dict
    r.META['CONTENT_TYPE'] = 'application/json'
    ProjectBuildListHandler().create(r, info.get('package'))
    return "Processed Correctly"



def check_should_build(client_info, True, reserve_time):
    return (True, "We always build, now!")

dispatcher.register_function(add_results, 'add_results')
dispatcher.register_function(check_should_build, 'check_should_build')
