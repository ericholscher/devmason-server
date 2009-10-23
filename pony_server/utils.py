"""
Piston API helpers.
"""

import mimeparse
import piston.resource
import piston.emitters
import piston.handler
import piston.utils
from django.core import urlresolvers
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import dateformat
from django.utils.http import urlencode

class Resource(piston.resource.Resource):
    """Chooses an emitter based on mime types."""
    
    def determine_emitter(self, request, *args, **kwargs):
        # First look for a format hardcoded into the URLconf
        em = kwargs.pop('emitter_format', None)
        
        # Then look for ?format=json
        if not em:
            em = request.GET.get('format', None)
            
        # Then try the accept header
        if not em and 'HTTP_ACCEPT' in request.META:
            mime = mimeparse.best_match(['application/json', 'text/html'],
                                        request.META['HTTP_ACCEPT'])
            if mime:
                em = mime.split('/')[-1]
                
        # Finally fall back on HTML
        return em or 'html'
        
class HTMLTemplateEmitter(piston.emitters.Emitter):
    """Emit a resource using a good old fashioned template."""
    
    def render(self, request):
        return render_to_response(
            template = 'pony/%s.html' % self.handler.__name__.lower(),
            context = self.data,
            context_instance = RequestContext(request),
        )

piston.emitters.Emitter.register(HTMLTemplateEmitter, 'html', 'text/html')

def link(rel, to_handler, *args, **getargs):
    """
    Create a link resource - a dict with rel, href, and allowed_methods keys.
    Extra args taken by the view may be passed in as *args; GET may be passed
    as **kwargs.
    """
    href = urlresolvers.reverse(to_handler.viewname, args=args)
    if getargs:
        href = "%s?%s" % (href, urlencode(getargs))
    return {
        'rel': rel,
        'href': href,
        'allowed_methods': to_handler.allowed_methods
    }
    
# Needed now; will be fixed in Piston 0.2.3
def allow_404(func): 
    """ 
    decorator that catches Http404 exceptions and safely returns 
    piston style 404 responses (rc.NOT_FOUND). 
    """ 
    def wrapper(*args, **kwargs): 
        try: 
            return func(*args, **kwargs) 
        except Http404: 
            return piston.utils.rc.NOT_FOUND 
    return wrapper

def format_dt(dt):
    return dateformat.format(dt, 'r')