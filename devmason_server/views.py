try:
    import json
except:
    import simplejson as json

import datetime
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.handlers.wsgi import WSGIRequest
from django.template import RequestContext


from devmason_server.models import Repository, BuildRequest, Project
from devmason_server.handlers import ProjectBuildListHandler
from devmason_utils.utils import slugify
from devmason_server.forms import ProjectForm

def add_project(request, template_name='devmason_server/add_project.html'):
    """
    Add project

    Template: ``projects/new_project.html``
    Context:
        form
            Form object.
    """
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project, created = Project.objects.get_or_create(name=form.cleaned_data['name'],
                                                         slug=slugify(form.cleaned_data['name']))
        repo, created = Repository.objects.get_or_create(
         url=form.cleaned_data['source_repo'],
         project=project,
        )
        return HttpResponseRedirect(project.get_absolute_url())
    return render_to_response(template_name, {'form': form},
            context_instance=RequestContext(request))

def claim_project(request, slug):
    project = Project.objects.get(slug=slug)
    project.owner = request.user
    project.save()
    return HttpResponse('Project has been claimed')

def github_build(request):
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
    return HttpResponse('Build Started')

def bitbucket_build(request):
    obj = json.loads(request.POST['payload'])
    rep = obj['repository']
    name = rep['name']
    url = "%s%s" % ("http://bitbucket.org",  rep['absolute_url'])
    hash = obj['commits'][0]['node']

    project = Project.objects.get(slug=name)
    repo, created = Repository.objects.get_or_create(
         url=url,
         project=project,
         type='hg',
    )
    brequest = BuildRequest.objects.create(
        repository = repo,
        identifier = hash,
        requested = datetime.datetime.utcnow(),
    )
    return HttpResponse('Build Started')

def request_build(request):
    obj = json.loads(request.raw_post_data)
    project = obj['project']
    identifier = obj['identifier']
    repo = Repository.objects.get(project__slug=project)
    brequest = BuildRequest.objects.create(
        repository = repo,
        identifier = identifier,
        requested = datetime.datetime.utcnow(),
    )
    return HttpResponse('Build Started')

### Crazy XMLRPC stuff below here.

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
                    'started': info.get('start_time', ''),
                    'finished': info.get('end_time', ''),
                    'tags': info['tags'],
                    'client': {
                        'arch': info.get('arch', ''),
                        'host':info.get('host', ''),
                        'user': 'pony-client',
                            },
                    'results': []
                }

    for result in results:
        success = False
        #Status code of 0 means successful
        if result.get('status', False) == 0:
            success = True
        build_dict['results'].append(
                       {'success': success,
                        'name': result.get('name', ''),
                        'errout': result.get('errout', ''),
                        'output': result.get('output', ''),
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
    package = unicode(info.get('package'))
    try:
        pro, created = Project.objects.get_or_create(name=package, slug=slugify(package))
    except:
        pass
    ProjectBuildListHandler().create(r, package)
    return "Processed Correctly"



def check_should_build(client_info, True, reserve_time):
    return (True, "We always build, now!")

dispatcher.register_function(add_results, 'add_results')
dispatcher.register_function(check_should_build, 'check_should_build')
