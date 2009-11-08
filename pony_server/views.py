def start_build(request):
       import ipdb; ipdb.set_trace()
       obj = simplejson.loads(request.POST['payload'])
       url = obj['repository']['url']
       hash = obj['after']
       git_url = url.replace('http://', 'git://')
