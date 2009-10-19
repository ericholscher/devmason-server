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

class BaseHandler(piston.handler.BaseHandler):
    """
    Base class for all handlers in pony_server. Adds:
    
        * Helper for building the links element.
    """
    
    # Child classes should set this.
    viewname = None
    
    def build_links(self, request, *args):
        """
        Build a list of Link resources - dicts with rel, href, and
        allowed_methods keys. Each *args argument is a (rel, handler) pair.
        Extra args taken by the view may be passed in as extra elements in the
        args tuples.
        """
        links = []
        for arg in args:
            rel, handler = arg[0:2]
            rest = arg[2:]
            links.append({
                'rel': rel,
                'href': handler.uri(request, *rest),
                'allowed_methods': handler.allowed_methods
            })
        return links
    
    @classmethod
    def uri(cls, request, *args):
        """Return the full URI for this handler, including host."""
        return request.build_absolute_uri(urlresolvers.reverse(cls.viewname, args=args))

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
            return rc.NOT_FOUND 
    return wrapper

