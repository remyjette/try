This module grades student code using the "cs3110 test" command, which is
a wrapper around pa_ounit.

For more information, see https://github.com/cs3110/tools

The pa_ounit library does not provide an easy way to get test results - it just
sends them to stdout or a file, so previously the only way to see test results
was to scrape them, which was quite error-prone as only failures would be
displayed: if an error occurred, no failures would be found so the harness
would assume all tests passed.

To remedy this, the "pa_ounit" subdirectory contains an updated pa_ounit library
to implement a function Pa_ounit_lib.Runtime.results which provides the results
as a list of testname and result pairs. The result clearly indicates whether
the test passed or failed. It can be installed by just using "opam pin" with the
path.

The "tester" directory creates a basic Flask application to listen for requests,
compile and run the given test file, and use Yojson to convert the test results
list into a JSON response. It can be run directly to use Flask's development
webserver, or can be called via WSGI like any other flask application.

A Dockerfile and associated configurations are provided to easily spin this
testing module up as a Docker container to provide isolation, using nginx
and gunicorn to serve web requests.
