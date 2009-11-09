try:
    import json
except:
    import simplejson as json

import datetime
from pony_server.models import Repository, BuildRequest, Project

def start_build(request):
    obj = json.loads(request.POST['payload'])
    name = obj['repository']['name']
    url = obj['repository']['url']
    git_url = url.replace('http://', 'git://')
    hash = obj['after']

    import ipdb; ipdb.set_trace()
    project = Project.objects.get(slug=name)
    repo = Repository.objects.get_or_create(url=git_url)
    brequest = BuildRequest.objects.create(
        repository = repo,
        identifier = hash,
        requested = datetime.datetime.utcnow(),
    )
