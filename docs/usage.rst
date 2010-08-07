Usage
=====

Using the server is pretty simple. Most of the interaction is done through the API, which has a basic client library. The client library is located on github: http://github.com/ericholscher/devmason-utils/.

Using the test runner
---------------------

Once you have `devmason_utils` installed, it ships with it's own test runner that reports your test results to the server. Simply add the following in your settings::

    TEST_RUNNER = 'devmason_utils.test_runner.run_tests'
    PB_USER = 'your_user'
    PB_PASS = 'your_pass'

When you do this the username will be created for your on the server, then your results should automatically be sent to http://devmason.com.

.. note::

    A username and password is only required to create a project. If you're
    just sending results to someone else's project then you only need to set up
    your test runner.
