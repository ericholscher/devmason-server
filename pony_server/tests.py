import pprint
import difflib
from django.test import TestCase, Client
from django.utils import simplejson

class PonyTests(TestCase):
    urls = 'pony_server.urls'
    fixtures = ['pony_server_test_data']
    
    def setUp(self):
        # Make a couple of clients with default Accept: headers to trigger the
        # dispatching based on mime type.
        self.api_client = Client(HTTP_ACCEPT='application/json')
        self.client = self.web_client = Client(HTTP_ACCEPT='text/html')

    def assertJsonEqual(self, response, expected):
        try:
            json = simplejson.loads(response.content)
        except ValueError:
            self.fail('Response was invalid JSON:\n%s' % response)
        
        # inspired by
        # http://code.google.com/p/unittest-ext/source/browse/trunk/unittestnew/case.py#698
        self.assert_(isinstance(json, dict), 'JSON response is not a dictionary: \n%r')
        self.assert_(isinstance(expected, dict), 'Expected argument is not a dictionary.')
        if json != expected:
            diff = difflib.ndiff(pprint.pformat(expected).splitlines(), 
                                 pprint.pformat(json).splitlines())
            msg = ('\n' + '\n'.join(diff))
            self.fail(msg)

    def test_package_list(self):
        r = self.api_client.get('/')
        self.assertJsonEqual(r,
            {u'projects': [
                {u'name': u'pony',
                 u'owner': u'',
                 u'slug': u'pony',
                 u'links': [
                    {u'allowed_methods': [u'GET'], u'href': u'/pony', u'rel': u'self'},
                    {u'allowed_methods': [u'GET'], u'href': u'/pony/builds', u'rel': u'build-list'}
                  ]}],
             u'links': [
                {u'allowed_methods': [u'GET'], u'href': u'/', u'rel': u'self'}]})
        
    def test_package_detail(self):
        r = self.api_client.get('/pony')
        self.assertJsonEqual(r,
            {u'name': 'pony',
             u'owner': '',
             u'slug': 'pony',
             u'links': [
                {u'allowed_methods': [u'GET'], u'href': u'/pony', u'rel': u'self'},
                {u'allowed_methods': [u'GET'], u'href': u'/pony/builds', u'rel': u'build-list'}]})
        
    def test_package_build_list(self):
        r = self.api_client.get('/pony/builds')
        self.assertJsonEqual(r, 
            {u'count': 1,
             u'num_pages': 1,
             u'page': 1,
             u'paginated': False,
             u'per_page': 25,
             u'builds': [{u'success': True,
                          u'started': u'Mon, 19 Oct 2009 16:22:00 -0500',
                          u'finished': u'Mon, 19 Oct 2009 16:25:00 -0500',
                          u'tags': [],
                          u'client': {u'host': u'example.com', 
                                      u'user': u'', 
                                      u'arch': u'linux-i386'},
                          u'results': [
                            {u'errout': u'',
                             u'finished': u'Mon, 19 Oct 2009 16:25:00 -0500',
                             u'name': u'test',
                             u'output': u'OK',
                             u'started': u'Mon, 19 Oct 2009 16:21:30 -0500',
                             u'success': True},
                            {u'errout': u'',
                             u'finished': u'Mon, 19 Oct 2009 16:21:00 -0500',
                             u'name': u'checkout',
                             u'output': u'OK',
                             u'started': u'Mon, 19 Oct 2009 16:22:00 -0500',
                             u'success': True}],
                          u'links': [
                            {u'allowed_methods': [u'GET'], u'href': u'/pony/builds/1', u'rel': u'self'},
                            {u'allowed_methods': [u'GET'], u'href': u'/pony', u'rel': u'project'}]}],
             u'links': [
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/builds?per_page=25&page=1',
                 u'rel': u'self'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony',
                 u'rel': u'project'}]})