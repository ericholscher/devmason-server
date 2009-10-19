from SimpleXMLRPCServer import SimpleXMLRPCDispatcher
from django.http import HttpResponse
from pony_server.models import Client, Result, Package, Tag
from django.template.defaultfilters import slugify
from django.shortcuts import render_to_response
from django.views.generic import list_detail

def index(request):
    ret_val = {}
    qs = Client.objects.all()
    for client in qs:
        print client
        if ret_val.has_key(client.package.name):
            ret_val[client.package.name].append(client)
        else:
            ret_val[client.package.name] = [client]

    return render_to_response('pony_server/client_list.html',
                              {'object_list': ret_val})
    return list_detail.object_list(request, queryset=qs)

def package_list(request, slug):
    qs = Result.objects.filter(client__package__slug=slug)
    return list_detail.object_list(request, queryset=qs)

def result_detail(request, slug, id):
    qs = Result.objects.filter(client__package__slug=slug)
    return list_detail.object_detail(request, qs, object_id=id)


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
                help =  dispatcher.system_methodHelp(method)
                response.write("<li><b>%s</b>: [%s] %s" % (method, sig, help))
        response.write("</ul>")
        response.write('<a href="http://www.djangoproject.com/"> <img src="http://media.djangoproject.com/img/badges/djangomade124x25_grey.gif" border="0" alt="Made with Django." title="Made with Django."></a>')


    response['Content-length'] = str(len(response.content))
    return response



def add_results(info, results):
    "Return sweet results"
    p = info.get('package', '')
    package, created = Package.objects.get_or_create(name=p, slug=slugify(p))

    client, created = Client.objects.get_or_create(
        arch=info.get('arch', ''),
        host=info.get('host', ''),
        tempdir=info.get('tempdir', ''),
        package=package,
        success=info.get('success', False),
        duration=info.get('duration', 0)
    )

    for tag in info['tags']:
        t, created = Tag.objects.get_or_create(name=tag, slug=slugify(tag))
        client.tags.add(t)

    for result in results:
        res, created = Result.objects.get_or_create(
            name=result.get('name', ''),
            slug=slugify(result.get('name', '')),
            command = result.get('command', ''),
            out = result.get('out', ''),
            errout = result.get('errout', ''),
            status = result.get('status', None),
            #Should probably be a FK
            type = result.get('type', ''),
            version_type = result.get('version_type', ''),
            version_info = result.get('version_info', ''),
            client = client,
        )
    return 'Sweet Processed'

def check_should_build(client_info, True, reserve_time):
    try:
        p = Package.objects.get(slug=client_info['package'])
        client = p.clients.get(host=client_info['host'])
        tag = client.tags.filter(slug__istartswith='svn')[0]
        print tag
        #return (tag in client_info['tags'], 'WOOOOOOO')
    except:
        pass
    return (True, "We always build, now!")

dispatcher.register_function(add_results, 'add_results')
dispatcher.register_function(check_should_build, 'check_should_build')
