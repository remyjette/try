from autograder import app, db
from autograder.models import Course, Assignment, Log, Testfile, Unittest
from flask import render_template, request, abort, flash, Blueprint, g
from werkzeug import secure_filename
import flask
import json
import tempfile
import os
import itertools
import requests
import sys

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/<course_name>/")
@main.route("/<course_name>/<assignment_name>/")
def index(course_name = None, assignment_name = None):
  """
  The main homepage of the autograder site. Students can see their courses,
  select a course to view assignments, and then select an assignment to render
  the upload form for use in uploading their code.
  """
  courses = Course.accessible_by(request.username)
  course = None
  assignments = None
  assignment = None

  if course_name is not None:
    course = next((c for c in courses if c.name == course_name), None)
    if course is None:
      return abort(404)
    # Only show public unit tests
    assignments = course.assignments.filter_by(visible=True).filter(Assignment.testfiles.any(Testfile.unittests.any(Unittest.is_public)))
    if course is not None and assignment_name is not None:
      assignment = assignments.filter_by(name=assignment_name).first_or_404()

  return render_template("main.html", courses=courses, course=course, assignments=assignments, assignment=assignment)


@main.route("/<course_name>/<assignment_name>/test/", methods=["POST"])
def test(course_name, assignment_name):
  """This function takes a student submission, runs the testfiles for this
  assignment, and returns a JSON response of the test results for tests that
  are publicly visible.

  Called via ajax in the frontend code, which is responsible for rendering the
  test results on the page.
  """

  course = Course.query.filter_by(name=course_name).first()

  if not course.can_access(request.username):
    return abort(403)

  assignment = course.assignments.filter_by(name=assignment_name).first()

  with tempfile.TemporaryDirectory() as tempdir:
    submission = request.files['submission']
    submission.save(os.path.join(tempdir, secure_filename(submission.filename)))

    try:
      results = {testfile.filename: testfile.grade(
          [os.path.join(tempdir, secure_filename(submission.filename))]
        )
        for testfile in assignment.testfiles.filter(Testfile.unittests.any(Unittest.is_public))}
    except requests.exceptions.ConnectionError as e:
      #Log the exception, then flash a message to the user
      app.log_exception(sys.exc_info())
      error_message = "Error contacting grader host. Please contact an administrator."
      flash(error_message, "error")
    except json.JSONDecodeError as e:
      #Log the exception, then flash a message to the user
      app.log_exception(sys.exc_info())
      error_message = "Error decoding results. Please contact an administrator."
      flash(error_message, "error")

    messages = flask.get_flashed_messages(with_categories=True)
    if messages:
      for category, message in messages:
        if category == "error":
          return json.dumps({"error": message})

    non_failure_results = {k: v["results"] for k,v in results.items() if "results" in v}
    test_bool_results = [t["passed"] for t in
                            itertools.chain.from_iterable(non_failure_results.values())]
    log = Log(
      request.username,
      len(list(filter(None, test_bool_results))),
      len(test_bool_results),
      json.dumps(results)
    )
    db.session.add(log)
    db.session.commit()

  return json.dumps(results)
