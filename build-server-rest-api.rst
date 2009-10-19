=====================
Build server REST API 
=====================

This is a proposed standard for a REST API for build clients to use to
communicate with a build server. It's inspired by pony-build, and generally
rather Python-oriented, but the goal is language-agnostic.

.. contents:: Contents

API Usage
=========

Registering a new project
-------------------------

.. parsed-literal::

    -> PUT /{project}
       
       {Project_}
       
    <- 201 Created
       Location: /{project}/builds/{build-id}
       
If a project already exists, a 403 Forbidden will be returned.

Users may register with authentication via HTTP Basic::

    -> PUT /{project}
       Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==
       
       {Project_}
       
    <- 201 Created
       Location: /{project}/builds/{build-id}

If this is done, then that authorization may be repeated in the future to
update/delete the project or to delete builds. No explicit user registration
step is needed; users will be created on the fly.

.. warning::

    Since the authorization uses HTTP Basic, build servers should probably
    support SSL for the security-conscious.
        
Reporting a build
-----------------

.. parsed-literal::

    -> POST /{project}/builds
       
       {Build_}
       
    <- 201 Created
       Location: /{project}/builds/{build-id}

Incremental build reporting
---------------------------

.. parsed-literal::

    -> POST /{project}/builds  
       
       {`Incremental build`_}
    
    <- 201 Created
       Location: /{project}/builds/{build-id}/progress
        
    -> POST /{project}/builds/{build-id}/progress
       
       {`Build step`_}
       
    <- 204 No Content
       Location: /{project}/builds/{build-id}
    
    -> POST /{project}/builds/{build-id}/progress
       
       {`Build step`_}
       
    <- 204 No Content
       Location: /{project}/builds/{build-id}
       
    
    ...
    
    -> DELETE /{project}/builds/{build-id}/progress
    
    <- 204 No Content
       Location: /{project}/builds/{build-id}

API Reference
=============

Representation formats
----------------------

JSON. UTF-8.

URIs
----

==============================================  ==================  ==================  ========================================
URI                                             Resource            Methods             Notes
==============================================  ==================  ==================  ========================================
``/``                                           `Project list`_     GET

``/{project}``                                  Project_            ``GET``, ``PUT``,   Only the user that created a project may
                                                                    ``DELETE``          update (``PUT``) or delete it.
                                                                    
``/{project}/builds``                           `Build list`_       ``GET``, ``POST``

``/{project}/builds/latest``                    --                   ``GET``            302 redirect to latest build.

``/{project}/builds/{build-id}``                Build_              ``GET``, ``PUT``,   Builds may not be updated; ``PUT`` only
                                                                    ``DELETE``          exists if clients wish for some reason
                                                                                        to use a predetermined build id. Only
                                                                                        the user that created a build or the 
                                                                                        project owner may delete a build.
                                                                                        
``/{project}/builds/{build-id}/progress``       `Build progress`_   ``GET``, ``POST``,
                                                                    ``DELETE``

``/{project}/tags``                             `Tag list`_         ``GET``

``/{project}/tags/{-listjoin|-|tags}``          `Build list`_       ``GET``

``/{project}/tags/{-listjoin|-|tags}/latest``   --                  ``GET``             302 redirect to latest build given tags
                                                                                        
``/users``                                      `User list`_        ``GET``

``/users/{username}``                           `User`_             ``GET``, ``PUT``,   Authentication required to ``PUT`` or
                                                                    ``DELETE``          ``DELETE``.

``/users/{username}/builds``                    `Build list`_       ``GET``

``/users/{username}/builds/latest``             --                  ``GET``             302 redirect to latest build by user
==============================================  ==================  ==================  ========================================

All resources support ``OPTIONS`` which will return a list of allowed methods
in the ``Allow`` header. This is particularly useful to check authentication
for methods that require it.

Resources
---------

Build
~~~~~

Representation:

.. parsed-literal::

    {
      'success': true,                              # did the build succeed?
      'started': 'Mon Oct 19 11:33:37 CDT 2009',
      'finished': 'Mon Oct 19 11:35:41 CDT 2009,
      
      'tags': ['list', 'of', 'tags'],
      
      'client': {
        'host': 'example.com',                      # host that ran the build
        'user': 'http://example.com/'               # user to credit for build.
        'arch': 'macosx-10.5-i386'                  # architecture the build was done on.
        ... [#]_
      },
      
      'results': [{`Build step`_}, ...],
      
      'links': [{Link_}, ...]
    }
    
Notes:
    
.. [#] Clients may include arbitrary extra client info in the client record.

Links:

===========  ======================================================
Rel          Links to                                            
===========  ======================================================
``self``     This `build`_                                  
``project``  The project_ this is a builds of.          
``tag``      A tag_ this build is tagged with. There'll probably be
             many ``tag`` links.
===========  ======================================================

Build list
~~~~~~~~~~

Representation:

.. parsed-literal::

    {
      'builds': [{Build_}, ...],
      
      'count': 100,                 # total number of builds available
      'num_pages': 4,               # total number of pages
      'page': 1                     # current page number
      'paginated': true             # is this list paginated?
      'per_page': 25,               # number of builds per page
      
      'links': [{Link_, ...}]
    }
    
Links:

================  ====================================================
Rel               Links to                                            
================  ====================================================
``self``          This `build list`_                                  
``project``       The project_ this is a list of builds for.          
``latest-build``  URI for the redirect to this project's latest build.
``next``          The next page of builds (if applicable).            
``previous``      The previous page of builds (if applicable).        
``first``         The first page of builds.                           
``last``          The last page of builds.                            
================  ====================================================

Build progress
~~~~~~~~~~~~~~

Used as an entry point for `incremental build reporting`_

Empty representation -- the existence of the resource indicates an in-progress
build. When the build is done, the resource will return 410 Gone.

Build step
~~~~~~~~~~

Representation:

.. parsed-literal::

    {
      'success': true,                              # did this step succeed?
      'started': 'Mon Oct 19 11:33:37 CDT 2009',
      'finished': 'Mon Oct 19 11:35:41 CDT 2009,
      'name': 'checkout',                           # human-readable name for the step
      'output': '...'                               # stdout for this step
      'errout': '...'                               # stderr for this step
      ... [#]_
    }
    
Notes:

.. [#] Build steps may include arbitrary extra build info in the record.


Incremental build
~~~~~~~~~~~~~~~~~

``POST`` this resource to a `build list`_ to signal the start of an incremental build.

Representation

.. parsed-literal::

    {
      'incremental': true,                          # never false
      'started': 'Mon Oct 19 11:33:37 CDT 2009',    # when the build started on
                                                    # the client (not when the
                                                    # packet was posted!)
      'client': {
        'host': 'example.com',                      # host that ran the build
        'user': 'username'                          # user to credit for build.
        'arch': 'macosx-10.5-i386'                  # architecture the build was done on.
        ... [#]_
      },
      
      'tags': ['list', 'of', 'tags'],
    }
    
Notes:

.. [#] Clients may include arbitrary extra client info in the client record.

Link
~~~~

Used all over the damn place to knit resources together.

Representation::

    {
        'rel': 'self',                  # identifier for the type of link this is
        'href': 'http://example.com/',  # full URL href
        'allowed_methods': ['GET'],     # list of methods this client can perform on said resource
    }
    

Project
~~~~~~~

Representation:

.. parsed-literal::

    {
      'name': 'Project Name',
      'slug': 'project-slug',
      'owner': 'username',      # the user who created the project, if applicable.
      
      'links': [{Link_}, ...]
    }
    
Links:

================ ====================================================
Rel              Links to                                            
================ ====================================================
``self``         This project_.                                      
``build-list``   This project's `build list`_.                       
``latest-build`` URI for the redirect to this project's latest build.
``tag-list``     This project's `tag list`_.                         
================ ====================================================

Project list
~~~~~~~~~~~~

.. parsed-literal::

    {
      'projects': [{Project_}, ...],
      'links': [{Link_}, ...]
    }

Links:

========  ============
Rel       Links to    
========  ============
``self``  This server.
========  ============
    
Tag
~~~

A tag or set of tags.

.. parsed-literal::

    {
      'tags': ['list', 'of', 'tags'],       # Or just a single ['tag'] if this
                                            # is one tag.
      'builds': [{Build_}, ...],
      
      'count': 100,                         # total number of builds w/this tag
      'num_pages': 4,                       # total number of pages
      'page': 1                             # current page number
      'paginated': true                     # is this list paginated?
      'per_page': 25,                       # number of builds per page
      
      'links': [{Link_, ...}]
    }
    
Links:

===========  ======================================================
Rel          Links to                                            
===========  ======================================================
``self``     This `tag`_ (set)
``project``  The project_ in question.
===========  ======================================================

Tag list
~~~~~~~~

Representation:

.. parsed-literal::

    {
      'tags': [{Tag_}, ...],
      
      'count': 100,                 # total number of tags available
      'num_pages': 4,               # total number of pages
      'page': 1                     # current page number
      'paginated': true             # is this list paginated?
      'per_page': 25,               # number of tags per page
      'links': [{Link_, ...}]
    }
    
Links:

===========  ======================================================
Rel          Links to                                            
===========  ======================================================
``self``     This `tag list`_                                  
``project``  The project_ in question.
===========  ======================================================

User
~~~~

Representation:

.. parsed-literal::

    {
      'username': 'username',
      'links': [{Link_}, ...]
    }

Links:

===========  ======================================================
Rel          Links to                                            
===========  ======================================================
``self``     This `user`_
``builds``   `Build list`_ for this user.
===========  ======================================================


User list
~~~~~~~~~

Representation:

.. parsed-literal::

    {
      'users': [{User_}, ...],
      
      'count': 100,                 # total number of users available
      'num_pages': 4,               # total number of pages
      'page': 1                     # current page number
      'paginated': true             # is this list paginated?
      'per_page': 25,               # number of users per page
      'links': [{Link_, ...}]
    }

Links:

===========  ======================================================
Rel          Links to                                            
===========  ======================================================
``self``     This `user`_
===========  ======================================================

