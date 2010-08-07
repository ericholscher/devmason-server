"""
Piston API helpers.
"""

import unicodedata
import re
import time
import datetime
import functools
import mimeparse
import email.utils
import piston.resource
import piston.emitters
import piston.handler
import piston.utils
from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.core import urlresolvers
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import dateformat
from django.utils.http import urlencode

# Try to use dateutil for maximum date-parsing niceness. Fall back to
# hard-coded RFC2822 parsing if that's not possible.
try:
    import dateutil.parser
except ImportError:
    dateutil = None

class Resource(piston.resource.Resource):
    """Chooses an emitter based on mime types."""

    def determine_emitter(self, request, *args, **kwargs):
        # First look for a format hardcoded into the URLconf
        em = kwargs.pop('emitter_format', None)

        # Then look for ?format=json
        if not em:
            em = request.GET.get('format', None)

        # Finally fall back on HTML
        return em or 'html'

class HTMLTemplateEmitter(piston.emitters.Emitter):
    """Emit a resource using a good old fashioned template."""

    def render(self, request):
        if isinstance(self.data, HttpResponse):
            return self.data
        if isinstance(self.data, models.Model):
            context = {self.data._meta.object_name.lower(): self.data,
                       'links': self.construct()['links']}
        else:
            context = self.data
        return render_to_response(
            'devmason_server/%s.html' % self.handler.viewname.lower(),
            context,
            context_instance = RequestContext(request),
        )

piston.emitters.Emitter.register('html', HTMLTemplateEmitter, 'text/html')

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

    def __init__(self):
        HttpResponse.__init__(self)
        self['WWW-Authenticate'] = 'Basic realm="pony"'

class HttpResponseCreated(HttpResponseRedirect):
    status_code = 201

class HttpResponseNoContent(HttpResponse):
    status_code = 204

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

def _get_user(request):
    """
    Pull a user out of the `Authorization` header. Returns the user, an
    `AnonymousUser` if there's no Authorization header, or `None` if there was
    an invalid `Authorization` header.
    """
    if 'HTTP_AUTHORIZATION' not in request.META or not request.META['HTTP_AUTHORIZATION']:
        return AnonymousUser(), None

    # Get or create a user from the Authorization header.
    try:
        authtype, auth = request.META['HTTP_AUTHORIZATION'].split(' ')
        if authtype.lower() != 'basic':
            return None
        username, password = auth.decode('base64').split(':')
        user = User.objects.get(username=username)
        user.is_new_user = False
    except ValueError:
        # Raised if split()/unpack fails
        return None
    except User.DoesNotExist:
        user = User(username=username)
        user.set_password(password)
        user.is_new_user = True

    return user, password

def authentication_required(callback):
    """
    Require that a handler method be called with authentication.

    Pony server has somewhat "interesting" authentication: new users are
    created transparently when creating new resources, so this needs to keep
    track of whether a user is "new" or not so that the handler may optionally
    save the user if needed. Thus, this annotates `request.user` with the user
    (new or not), and sets a `is_new_user` attribute on this user.
    """
    @functools.wraps(callback)
    def _view(self, request, *args, **kwargs):
        user, password = _get_user(request)
        if not user or user.is_anonymous():
            return HttpResponseUnauthorized()
        if not user.check_password(password):
            return HttpResponseForbidden()
        request.user = user
        return callback(self, request, *args, **kwargs)
    return _view

def authentication_optional(callback):
    """
    Optionally allow authentication for a view.

    Like `authentication_required`, except that if there's no auth info then
    `request.user` will be `AnonymousUser`.
    """
    @functools.wraps(callback)
    def _view(self, request, *args, **kwargs):
        user, password = _get_user(request)
        if not user:
            return HttpResponseUnauthorized()
        if user.is_authenticated() and not user.check_password(password):
            return HttpResponseForbidden()
        request.user = user
        return callback(self, request, *args, **kwargs)
    return _view

def format_dt(dt):
    return dateformat.format(dt, 'r')

# Try to use dateutil for maximum date-parsing niceness. Fall back to
# hard-coded RFC2822 parsing if that's not possible.
if dateutil:
    mk_datetime = dateutil.parser.parse
else:
    def mk_datetime(string):
        return datetime.datetime.fromtimestamp(time.mktime(email.utils.parsedate(string)))

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '_', value).strip().lower())
    return re.sub('[-\s]+', '-', value)


