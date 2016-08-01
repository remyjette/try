# The "Cornell Try" Autograding System.

This system allows students to run their codes against a suite of unit tests
while they're working on their assignemnts. Instructors can make test cases
available to students without necessarily exposing the test implementation.
Students can use this system to measure their progress as their submission
begins to pass the test cases, and it will allow them to ensure that any
differences between computing environments will not prevent their code from
running when it is graded. This same system can then be used by course staff to
evaluate all of the submissions for an assignment, and assign grades based on
the test cases that each submission passed.

Although originally developed for use by Cornell's CS 3110 course, it features
a modular architecture and can be used with any course or testing framework.

## Repository / system architecture

### `autograder` directory

This autograder is a web-based platform built using the Flask framework in
PYthon. This code is stored in the `autograder` directory in this repository,
and is responsible for receiving requests from both students and instructors
as well as storing data to organize the stored data into courses and
assignments. Requests to actually grade assignments are transmitted from this
part of the system to the grading module (see `modules` below).

Authentication should be handled externally to this system
and should be provided via a "Remote-User". Note that this means the system
should not be publically accessible, and should sit behind a reverse proxy
that will handle the authentication. The system then uses lists of admins,
instructioors, and students to handle authorization.

Any system using Python 3.5+ should be able to run this system (it will probably
work on earlier versions, it just hasn't been tested). Any method for hosting
a Flask WSGI application should work - scripts to start both the Flask
development server and hosting the app on gunicorn are in the `autograder`
directory.

This system stores a small amount of data about active courses and assignments
in a SQL database using SQLAlchemy - any database supported by SQLAlchemy
should work including SQLite.

### `web` directory

The web-based system does not actually grade any student code. To provide for
isolation between the central system and the grading hosts, allow easy
scalability, and enable flexibility in the grading framework used, the system
configuration simply maintains a list of grader servers that it can contact
to actually grade student assignments. When a grading request is received,
the system simply sends it to a random grading server and receives a list
of unit test passes and failures.

The main system doesn't care about the implementation of the grading servers,
only that it can accept a set of HTTP POST parameters:

* required_files - Optional. A list of files that must be present in the
submission. Allows us to return a better error message to accompany the no
compile mthan what would be returned if we just compiled against the release
code. If not provided, this check will be skipped.

* release - Optional. The release code. If it is a .zip archive, it'll be
extracted. If not provided, the test file will be compiled against the
student code with no additional files.

* submission# - Optional. a submitted file or .zip archive. Any files present
will replace release code files. Multiple files can be included, the POST
keys should be submission0, submission1, ..., submissionN. If not provided,
the test file will be compiled against the release code (for example to get
a list of the unit test names).

* test_file - The file containing unit tests to compile with the given code.

* timeout - Optional. How long (in seconds) to allow for a single grade request.
If exceeded, an error will be returned. Defaults to 60.

The grading server response should be as follows:

For an error that prevented any tests from being run:

    {
      "error": "<An error string>",
      "message": "A longer string describing the error"
    }

For example:

    {
      "error": "NO COMPILE",
      "message": "Unexpected ';' on line 12"
    }

When all tests were run (regardless of whether they passed/failed):

    {
      "results": [
        {
          "name": "Unit test name"
          "passed": true/false,
          "message": "Failure reason if 'passed' is false, null otherwise"
        },
        ...
      ]
    }

The `modules` directory contains two grading modules that conform to this spec.
One using the `cs3110 test` test runner (built upon pa_ounit), the other using
pyunit. Modules to use this system for running tests with other languages and
testing frameworks just need to conform to this spec.

To easily create new instances of these grading servers (and provide some
isolation if they are running on the same physical hardware as the central
system), both modules contain Dockerfiles to run the grading server within a
Docker container.

The main system and the graders can communicate over either HTTP or HTTPS -
if they are not running on the same physical hardware and this system is being
used in a production environment where students will be submitting code, HTTP
should NOT be used. If the graders don't have SSL certificates, self-signed
certificates can be used in a secure manner as the central system supports
loading custom certificate authority files.

## Using the system

### Setup

The `autograder` directory should deployed on a system that supports Python 3.5+.
For a production instance, `gunicorn` or some other runner should be used to
run the code, rather than the Flask development system. This server should *not*
be publically accessible - as mentioned above, some other server must provide
authentication and forward requests as a remote proxy.

Before running, the `config.cfg` file should be modified according to your
environment. This sets things like administrators, database configuration,
and the location of the grader servers, so make sure you set it up before
launching the system!

If using the modules in this repository, the can be run by simply deploying them
on any host that supports Linux-based Docker containers and using the included
Dockerfile.

## The instructor interface

Once deployed, simply navigate to the `/admin/` directory to access the
instructor interface. (For example, for the server deployed at
`https://try.cs.cornell.edu`, the instructor interface is available at
`https://try.cs.cornell.edu/admin/`).

When initially deployed, only users with usernames listed in the `ADMINS`
configuration in `config.cfg` will be able to access the system. They alone
have the power to create new courses. Once a course has been created,
instructors for that specific course can be set, and then those individuals
will have access to all the other functionality in the instructor interface. In
addition to being able to create courses, admins are treated as instructors for
all courses. Instructors also able to modify any of the details for their own
course, as well as delete it.

Course creation has the following options:

* Course name - The name of the course. Used in URLs for the course, so spaces
are not recommended.

* Visible to students - if unchecked, even students in the "Students" list below
will not see the course in the student interface.

* Instructors - A list of usernames for those who should have access to the
instructor interface for this course.

* Students - A list of usernames for those who should see this course in the
student interface and be able to submit single submissions for grading. Note:
Anyone in the 'Instructor' list is also given this permission.

* Default Timeout for New Test Files: The default timeout that will be used
when running tests on an individual submission. Can be overridden by the test
file configuration.

* Default Testing Engine: The testing engine that will be selected by default
for new test files in this course. Can be overridden by the test file
configuration. Populated by the `GRADER_SERVERS` configuration in `config.cfg`.

![Course Creation Screenshot](/screenshots/createcourse.png)

Once a course is created, instructors can add assignments. Assignments have
the following options:

* Assignment name - The name of the assignment. Like courses, the name is used
in URLs so spaces are not recommended.

* Visible to students - If unchecked, only instructors will see it in the
student interface.

* Release code - A single file (or .zip archive) that is the release code
provided to students at the beginning of the assignment. When submissions are
graded, the student's submission will be combined with the release code (with
any files with the same name in the submission overwriting the release files).
Useful when compilation requires interface files that the students do not submit.

* Max Score / Problems - Used to compute student scores when grading all
submissions (see below). If a max score is given, then a single score will
be provided in the grading output. If "Use Problems" is clicked, one can
define the problems in an assignment, each with its own maximum score. Then,
unit tests must be associated with a problem, and each problem score will be
computed only with the tests for that problem.

![Assignment Creation Screenshot](/screenshots/createassignment.png)

Once an assignment has been created, the test files will be displayed. Initially
no test files will be present, and the interface will allow you to upload one.
Test files have the following option:

* File - The path to the test file on your local machine.

* Testing Engine: The grading module to use for this test file.
Populated by the `GRADER_SERVERS` configuration in `config.cfg`.

* Required Files: A list of filenames that must be present in a student
submission. Any submission without these files will instantly fail all tests
with a "NO COMPILE" error. This prevents confusing error messages if (for
example) the student submits a .zip archive with an incorrect folder structure,
and so the system ends up running the tests against the release code.

* Timeout: The timeout (in seconds) for this test file. If running unit tests
exceeds this timer, the test will be cancelled and the submission will fail
with a "TIMEOUT EXCEEDED" error.

Uploading a test file causes it to be compiled and run with the selected
testing framework. If release code is provided for the assignment, it will be
copied to the same directory when the test file is run. This is done to
determine the names of the unit tests in the test file, so metadata can be
added through the instructor interface.

Once a test is added, the test file part of the interface will expand to show
all of the unit tests in that file. Each unit test has the following options:

* Test name - The name of the test. In the event that the framework does not
display useful names or includes unnecessary information like the line number of
the test, the name displayed to students can be changed.

* Public Test - Whether or not this test is made public to students. If checked,
the test will be included in results in the student interface, otherwise it will
only be used to compute scores for the assignment.

* Weight - The weighting of the test. Defaults to 1. The number itself means
nothing, only it's relation to the other tests. If all tests for a given
assignment have the same weight value, each test will be worth a number of
points equal to the number of tests in that problem/assignment divided by
the maxmimum score for that problem/assignment. If one test has a weight value
that is double that of another test, it will be worth twice as much. If 0,
the test will not be used.

* Problem - If problems are used for this assignment (see above), this test
will contribute to the score for the selected problem.

![Assignment Creation Screenshot](/screenshots/modifytestfile.png)

The last part of the instructor interface is the "grade all" functionality.
In the assignment management page, there is a section to upload and grade
all submissions for a course. The uploaded archive must have the following
structure:

    archive.zip
    └ Submissions/
      ├ netid1/
      │ └ <files for student submission>
      ├ netid2/
      │ └ <files for student submission>
      └ netid3/
        └ <files for student submission>

The output will use the directory names (netid1 and so on above) as the
first column in the grading output. If the name is "group_of_user1_user2",
the output will have a separate row for user1 and user2. Note that input
archive structure and the output names are specific to Cornell CMS. If using
this with another course management system, the code in
`web/autograder/grade_assignment.py` will likely need to be modified.

The grade all function will run each test file on each student submission,
compute scores using the weights defined above, and produce a CSV of the student
scores (with comments so students can know which tests they failed and, if
provided by the test framework, why) as well as some visualizations and statistics
of the student results on the assignment and each problem.

### The student interface

After logging in (see "system architecture" above, students
will be presented with a list of courses for which they are
enrolled. Any active assignments with public test cases will be listed, and
clicking on them will show a form for a student to upload their submission.

Upon upload, the code will be graded and results for public tests will be
returned.

![Student Interface Screenshot](/screenshots/studentinterface.png)
