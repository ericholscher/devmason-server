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
            self.fail('Response was invalid JSON')
        
        # see http://code.google.com/p/unittest-ext/source/browse/trunk/unittestnew/case.py#698
        self.assert_(isinstance(json, dict), 'JSON response is not a dictionary.')
        self.assert_(isinstance(expected, dict), 'Expected argument is not a dictionary.')
        if json != expected:
            msg = ('\n' + '\n'.join(difflib.ndiff(
                   pprint.pformat(json).splitlines(),
                   pprint.pformat(expected).splitlines())))
            self.fail(msg)

    def test_package_list(self):
        r = self.api_client.get('/')
        self.assertJsonEqual(r, {
            'projects': [
                {
                    'name': 'pony',
                    'owner': '',
                    'slug': 'pony'
                }
            ],
            'links': [
                {
                    'allowed_methods': ['GET'],
                    'href': 'http://testserver/',
                    'rel': 'self'
                }
            ],
        })
        
    def test_package_detail(self):
        r = self.api_client.get('/pony')
        self.assertJsonEqual(r, {
            'name': 'pony',
            'owner': '',
            'slug': 'pony',
            'links': [
                {
                    'allowed_methods': ['GET'],
                    'href': 'http://testserver/pony',
                    'rel': 'self',
                }
            ]
        })
        