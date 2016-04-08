from autograder import app, db
from autograder.grader import grade
from autograder.models import Course, Assignment, Testfile
from autograder.util import save_or_extract
from flask import render_template, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
import json
import shlex
import subprocess
import tempfile
import os
import zipfile

@app.route("/")
@app.route("/<course_name>/")
@app.route("/<course_name>/<assignment_name>/")
def index(course_name = None, assignment_name = None):
  course = None
  assignment = None

  if course_name is not None:
    course = Course.query.filter_by(name=course_name).first()
    if course is not None and assignment_name is not None:
      assignment = course.assignments.filter_by(name=assignment_name).first()

  courses = Course.query.all()
  return render_template("index.html", courses=courses, course=course, assignment=assignment)

@app.route("/<course_name>/<assignment_name>/test/", methods=["POST"])
def test(course_name, assignment_name):
  course = Course.query.filter_by(name=course_name).first()
  assignment = course.assignments.filter_by(name=assignment_name).first()

  submission = request.files['submission']

  with tempfile.TemporaryDirectory() as tempdir:
    save_or_extract(submission, tempdir)

    results = {testfile.filename: grade(tempdir, testfile, assignment.release_code_dir)
      for testfile in assignment.testfiles}

    return json.dumps(results)

@app.route("/admin/", methods=["GET", "POST"])
@app.route("/admin/<course_name>/", methods=["GET", "POST"])
@app.route("/admin/<course_name>/<assignment_name>/", methods=["GET", "POST"])
def admin(course_name=None, assignment_name=None):
  course = None
  assignment = None

  if request.method == "POST" and "new_course_name" in request.form:
    new_course = Course(request.form["new_course_name"], "")
    db.session.add(new_course)
    db.session.commit()

  if course_name is not None:
    course = Course.query.filter_by(name=course_name).first()

    if request.method == "POST" and "new_assignment_name" in request.form:
      new_assignment = Assignment(request.form["new_assignment_name"], "", course)
      db.session.add(new_assignment)
      db.session.commit()

      try:
        os.makedirs(new_assignment.release_code_dir, exist_ok=True)
        f = request.files['release-code']
        save_or_extract(f, new_assignment.release_code_dir)
      except:
        db.session.delete(new_assignment)
        db.session.commit()
        raise

    if course is not None and assignment_name is not None:
      assignment = course.assignments.filter_by(name=assignment_name).first()

      if request.method == "POST" and "testfile_name" in request.form:
        f = request.files['test-file']
        filename = secure_filename(f.filename)

        testfile_dir = os.path.join(app.config["TESTFILE_DIR"], assignment.directory_name)
        os.makedirs(testfile_dir, exist_ok=True)

        f.save(os.path.join(testfile_dir, filename))
        testfile = Testfile(filename, assignment)
        db.session.add(testfile)
        db.session.commit()

  courses = Course.query.all()
  return render_template("admin.html", courses=courses, course=course, assignment=assignment)
