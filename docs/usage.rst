Usage
=====

Using the server is pretty simple. Most of the interaction is done through the API, which has a basic client library. The client library is located on github: `http://github.com/ericholscher/devmason-utils/`_ .

Using the test runner
---------------------

Once you have `devmason_utils` installed, it ships with it's own test runner that reports your test results to the server. Simply add the following in your settings::

    TEST_RUNNER = 'devmason_utils.test_runner.run_tests'

Then your results should automatically be sent to `http://devmason.com`_.
