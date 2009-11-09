import pprint
import difflib
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import simplejson
from ..models import Build

class PonyTests(TestCase):
    urls = 'pony_server.urls'
    fixtures = ['authtestdata', 'pony_server_test_data']
    
    def setUp(self):
        # Make this class's test client have a default Accept: header to
        # trigger the dispatching to API methods.
        self.client = Client(HTTP_ACCEPT='application/json')
        
        # Tag us a build (this is hard from fixtures)
        b = Build.objects.get(pk=1)
        b.tags = 'python, django'
        b.save()

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

class PackageListTests(PonyTests):
    def test_get_package_list(self):
        r = self.client.get('/')
        self.assertJsonEqual(r, {
            u'projects': [{
                u'name': u'pony',
                u'owner': u'',
                u'links': [
                    {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                     u'href': u'/pony', 
                     u'rel': u'self'},
                    {u'allowed_methods': [u'GET', u'POST'],
                     u'href': u'/pony/builds',
                     u'rel': u'build-list'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/builds/latest',
                     u'rel': u'latest-build'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/tags',
                     u'rel': u'tag-list'},
                ]
            }],
            u'links': [{
                u'allowed_methods': [u'GET'], 
                u'href': u'/', 
                u'rel': u'self'
            }]
        })

class PackageDetailTests(PonyTests):
    def test_get_package_detail(self):
        r = self.client.get('/pony')
        self.assertJsonEqual(r, {
            u'name': u'pony',
            u'owner': u'',
            u'links': [
                {u'allowed_methods': [u'GET', u'PUT', u'DELETE'], 
                 u'href': u'/pony', 
                 u'rel': u'self'},
                {u'allowed_methods': [u'GET', u'POST'], 
                 u'href': u'/pony/builds', 
                 u'rel': u'build-list'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/builds/latest',
                 u'rel': u'latest-build'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/tags',
                 u'rel': u'tag-list'},
            ]
        })
        
    def test_create_new_package_fails_when_not_authenticated(self):
        r = self.client.put('/proj', data='{"name": "myproject"}', 
                                content_type="application/json")
        self.assertEqual(r.status_code, 401) # 401 unauthorized
        self.assertEqual(r['WWW-Authenticate'], 'Basic realm="pony"')
    
    def test_create_new_package_works_with_existing_user(self):
        auth = "Basic %s" % "testclient:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201, r.content) # 201 created
        self.assertEqual(r['Location'], 'http://testserver/proj')
        
        r = self.client.get('/proj')
        self.assertJsonEqual(r, {
            u'name': u'My Project',
            u'owner': u'testclient',
            u'links': [
                {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                 u'href': u'/proj', 
                 u'rel': u'self'},
                {u'allowed_methods': [u'GET', u'POST'],
                 u'href': u'/proj/builds', 
                 u'rel': u'build-list'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/proj/builds/latest',
                 u'rel': u'latest-build'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/proj/tags',
                 u'rel': u'tag-list'},
            ]
        })
        
    def test_create_new_package_creates_users_automatically(self):
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201, r.content) # 201 created
        self.assertEqual(r['Location'], 'http://testserver/proj')
        
        # Check that the user got created
        u = User.objects.get(username='testclient')
        self.assertEqual(u.check_password('password'), True)
        
    def test_update_package_succeeds_when_same_user(self):
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201) # 201 created
        
        r = self.client.put('/proj', data='{"name": "Renamed"}',
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertJsonEqual(r, {
            u'name': u'Renamed',
            u'owner': u'newuser',
            u'links': [
                {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                 u'href': u'/proj', 
                 u'rel': u'self'},
                {u'allowed_methods': [u'GET', u'POST'], 
                 u'href': u'/proj/builds', 
                 u'rel': u'build-list'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/proj/builds/latest',
                 u'rel': u'latest-build'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/proj/tags',
                 u'rel': u'tag-list'},
            ]
        })
        
    def test_update_package_fails_when_different_user(self):
        # the pony project was created with no auth, so this'll always fail
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/pony', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 403) # 403 forbidden
    
    def test_delete_package_succeeds_when_user_matches(self):
        # Create a package...
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201) # 201 created
        
        # ... and delete it
        r = self.client.delete('/proj', HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 204) # 204 no content
        
    def test_delete_package_fails_when_different_user(self):
        # Create a package...
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201) # 201 created
        
        # ... and delete it with different auth
        auth = "Basic %s" % "testclient:password".encode("base64").strip()
        r = self.client.delete('/proj', HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 403) # 403 forbidden
    
    def test_delete_package_should_not_create_users(self):
        # Create a package...
        auth = "Basic %s" % "newuser:password".encode("base64").strip()
        r = self.client.put('/proj', data='{"name": "My Project"}', 
                                content_type="application/json",
                                HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 201) # 201 created
        
        # ... and delete it with a new user
        auth = "Basic %s" % "newuwer2:password".encode("base64").strip()
        r = self.client.delete('/proj', HTTP_AUTHORIZATION=auth)
        self.assertEqual(r.status_code, 403) # 403 forbidden
        
        # newuser2 shouldn't have been created
        self.assertRaises(User.DoesNotExist, User.objects.get, username='newuser2')

class BuildListTests(PonyTests):
    def test_get_package_build_list(self):
        r = self.client.get('/pony/builds')
        self.assertJsonEqual(r, {
            u'count': 1,
            u'num_pages': 1,
            u'page': 1,
            u'paginated': False,
            u'per_page': 25,
            u'project': {
                u'name': u'pony',
                u'owner': u'',
                u'links': [
                    {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                     u'href': u'/pony',
                     u'rel': u'self'},
                    {u'allowed_methods': [u'GET', u'POST'],
                     u'href': u'/pony/builds',
                     u'rel': u'build-list'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/builds/latest',
                     u'rel': u'latest-build'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/tags',
                     u'rel': u'tag-list'}
                ],
            },
            u'builds': [{
                u'success': True,
                u'started': u'Mon, 19 Oct 2009 16:22:00 -0500',
                u'finished': u'Mon, 19 Oct 2009 16:25:00 -0500',
                u'tags': [u'django', u'python'],
                u'client': {u'host': u'example.com', u'user': u'', u'arch': u'linux-i386'},
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
                     u'success': True}
                ],
                u'links': [
                    {u'allowed_methods': [u'GET'], 
                     u'href': u'/pony/builds/1', 
                     u'rel': u'self'},
                    {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                     u'href': u'/pony',
                     u'rel': u'project'},
                    {u'allowed_methods': [u'GET'], 
                     u'href': u'/pony/tags/django', 
                     u'rel': u'tag'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/tags/python',
                     u'rel': u'tag'}
                ]   
            }],
            u'links': [
                {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                 u'href': u'/pony',
                 u'rel': u'project'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/builds/latest',
                 u'rel': u'latest-build'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/builds?per_page=25&page=1',
                 u'rel': u'self'},
            ]
        })
        
    def test_post_new_build(self):
        build = {
            u'success': False,
            u'started': u'Mon, 26 Oct 2009 16:22:00 -0500',
            u'finished': u'Mon, 26 Oct 2009 16:25:00 -0500',
            u'tags': [u'pony', 'build', 'rocks'],
            u'client': {u'host': u'example.com', u'user': u'', u'arch': u'linux-i386'},
            u'results': [
                {u'errout': u'',
                 u'finished': u'Mon, 26 Oct 2009 16:25:00 -0500',
                 u'name': u'test',
                 u'output': u'Step 1: OK',
                 u'started': u'Mon, 26 Oct 2009 16:21:30 -0500',
                 u'success': True},
                {u'errout': u'',
                 u'finished': u'Mon, 26 Oct 2009 16:21:00 -0500',
                 u'name': u'checkout',
                 u'output': u'Step 2: OK',
                 u'started': u'Mon, 26 Oct 2009 16:22:00 -0500',
                 u'success': False}
            ],
            u'extra1': u'hi',
            u'extra2': u'there',
        }
        
        r = self.client.post('/pony/builds', data=simplejson.dumps(build),
                             content_type='application/json')
        self.assertEqual(r.status_code, 201, r) # 201 created
        self.assertEqual(r['Location'], 'http://testserver/pony/builds/2')
        
        # make sure the build info came through okay
        r = self.client.get('/pony/builds/2')
        self.assertJsonEqual(r, build)

class LatestBuildTests(PonyTests):
    def test_get_latest_build(self):
        r = self.client.get('/pony/builds/latest')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], 'http://testserver/pony/builds/1')

class TagListTests(PonyTests):
    def test_get_tag_list(self):
        r = self.client.get('/pony/tags')
        self.assertJsonEqual(r, {
            u'tags': [u'django', u'python'],
            u'links': [
                {u'allowed_methods': [u'GET'], 
                 u'href': u'/pony/tags', 
                 u'rel': u'self'},
                {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                 u'href': u'/pony',
                 u'rel': u'project'},
                {u'allowed_methods': [u'GET'], 
                 u'href': u'/pony/tags/django', 
                 u'rel': u'tag'},
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/tags/python',
                 u'rel': u'tag'}
            ]
        })

class TagDetailTests(PonyTests):
    def test_get_tag_detail(self):
        r = self.client.get('/pony/tags/django')
        self.assertJsonEqual(r, {
            u'count': 1,
            u'num_pages': 1,
            u'page': 1,
            u'paginated': False,
            u'per_page': 25,
            u'tags': [u'django'],
            u'builds': [{
                u'success': True,
                u'started': u'Mon, 19 Oct 2009 16:22:00 -0500',
                u'finished': u'Mon, 19 Oct 2009 16:25:00 -0500',
                u'tags': [u'django', u'python'],
                u'client': {u'host': u'example.com', u'user': u'', u'arch': u'linux-i386'},
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
                     u'success': True}
                ],
                u'links': [
                    {u'allowed_methods': [u'GET'], 
                     u'href': u'/pony/builds/1', 
                     u'rel': u'self'},
                    {u'allowed_methods': [u'GET', u'PUT', u'DELETE'],
                     u'href': u'/pony',
                     u'rel': u'project'},
                    {u'allowed_methods': [u'GET'], 
                     u'href': u'/pony/tags/django', 
                     u'rel': u'tag'},
                    {u'allowed_methods': [u'GET'],
                     u'href': u'/pony/tags/python',
                     u'rel': u'tag'}
                ]   
            }],
            u'links': [
                {u'allowed_methods': [u'GET'],
                 u'href': u'/pony/tags/django?per_page=25&page=1',
                 u'rel': u'self'},
            ]
        })
        
class LatestTagsTests(PonyTests):
    def test_get_latest_tagged_build(self):
        r = self.client.get('/pony/tags/django/latest')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], 'http://testserver/pony/builds/1')
    
    def test_get_latest_tagged_build_404s_with_invalid_tags(self):
        r = self.client.get('/pony/tags/nope/latest')
        self.assertEqual(r.status_code, 404)