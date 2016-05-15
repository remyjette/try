from autograder import app, db
from autograder.models import Course, Assignment, Log, Testfile, Unittest
from flask import render_template, request, abort, flash, Blueprint
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
  course = None
  assignments = None
  assignment = None

  if course_name is not None:
    course = Course.query.filter_by(name=course_name).first_or_404()
    # Only show public unit tests
    assignments = course.assignments.filter_by(visible=True).filter(Assignment.testfiles.any(Testfile.unittests.any(Unittest.is_public)))
    if course is not None and assignment_name is not None:
      assignment = assignments.filter_by(name=assignment_name).first_or_404()

  courses = [c for c in Course.query.all() if c.can_access(request.username)]
  return render_template("main.html", courses=courses, course=course, assignments=assignments, assignment=assignment)


@main.route("/<course_name>/<assignment_name>/test/", methods=["POST"])
def test(course_name, assignment_name):

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
