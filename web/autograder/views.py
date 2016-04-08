from autograder import app, db
from autograder.models import Course, Assignment, Testfile, Unittest
from flask import render_template, request, session, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from autograder.grade_assignment import grade_assignment
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
  if "username" not in session:
    return redirect(url_for('login'))
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
  if "username" not in session:
    return abort(403)

  course = Course.query.filter_by(name=course_name).first()

  if not course.can_access(session["username"]):
    return abort(403)

  assignment = course.assignments.filter_by(name=assignment_name).first()

  with tempfile.TemporaryDirectory() as tempdir:
    submission = request.files['submission']
    submission.save(os.path.join(tempdir, secure_filename(submission.filename)))

    results = {testfile.filename: testfile.grade(
        [os.path.join(tempdir, secure_filename(submission.filename))]
      )
      for testfile in assignment.testfiles}

  return json.dumps(results)

@app.route("/admin/", methods=["GET", "POST"])
@app.route("/admin/<course_name>/", methods=["GET", "POST"])
@app.route("/admin/<course_name>/<assignment_name>/", methods=["GET", "POST"])
def admin(course_name=None, assignment_name=None):
  if "username" not in session:
    return redirect(url_for('login'))

  course = None
  assignment = None

  if request.method == "POST" and "new_course_name" in request.form:
    new_course = Course(request.form["new_course_name"], "")
    db.session.add(new_course)
    db.session.commit()

  if course_name is not None:
    course = Course.query.filter_by(name=course_name).first()

    if course is None:
      return abort(404)

    if not course.can_modify(session["username"]):
      return abort(403)

    if request.method == "POST" and "course_name" in request.form:
      course.name = request.form["course_name"]
      course.student_list = [username.strip() for username in request.form['student_list'].replace("@cornell.edu", "").split("\n") if username.strip()]
      db.session.commit()
      return redirect(url_for("admin", course_name=course.name))

    elif request.method == "POST" and "new_assignment_name" in request.form:
      new_assignment = Assignment(request.form["new_assignment_name"], "", course)
      db.session.add(new_assignment)
      db.session.commit()

      if "release-code" in request.files:
        try:
          os.makedirs(new_assignment.release_code_dir, exist_ok=True)
          f = request.files['release-code']
          new_assignment.release_filename = secure_filename(f.filename)
          f.save(new_assignment.release_code_file)
          db.session.commit()
        except:
          db.session.delete(new_assignment)
          db.session.commit()
          raise

    elif course is not None and assignment_name is not None:
      assignment = course.assignments.filter_by(name=assignment_name).first()

      if request.method == "POST" and "testfile_name" in request.form:
        f = request.files['test-file']
        filename = secure_filename(f.filename)

        testfile_dir = os.path.join(app.config["TESTFILE_DIR"], assignment.directory_name)
        os.makedirs(testfile_dir, exist_ok=True)

        f.save(os.path.join(testfile_dir, filename))
        testfile = Testfile(filename, assignment)

        testfile = assignment.testfiles.first()

        release_code_response = grade(
          open(testfile.filename, 'rb'),
          None,
          open(assignment.release_code_file, 'rb')
        )

        test_names = [result["name"] for result in release_code_response]
        for test_name in test_names:
          unittest = Unittest(test_name, testfile)
          db.session.add(unittest)

        db.session.add(testfile)
        db.session.commit()

      elif request.method == "POST" and "modify_unittests" in request.form:
        testfile = assignment.testfiles.filter_by(id=request.form["testfile_id"]).first()
        for unittest in testfile.unittests:
          form_testname_field = "name_" + str(unittest.id)
          form_weight_field = "weight_" + str(unittest.id)
          form_public_field = "public_" + str(unittest.id)
          if form_testname_field in request.form and form_weight_field in request.form:
            unittest.friendly_name = request.form[form_testname_field]
            unittest.weight = request.form[form_weight_field]
            unittest.is_public = form_public_field in request.form
            #unittest.is_public = request.form["public_" + unittest.id]
        db.session.commit()

  courses = Course.query.all()
  return render_template("admin.html", courses=courses, course=course, assignment=assignment)

@app.route("/admin/<course_name>/<assignment_name>/grade/", methods=["GET", "POST"])
def grade_submissions(course_name=None, assignment_name=None):
  if "username" not in session:
    return redirect(url_for('login'))

  if course_name is None:
    return abort(400)

  course = Course.query.filter_by(name=course_name).first()

  if course is None:
    return abort(404)

  if not course.can_modify(session["username"]):
    return abort(403)

  assignment = course.assignments.filter_by(name=assignment_name).first()

  submissions_archive = request.files['submissions_archive']

  return json.dumps(grade_assignment(assignment, submissions_archive))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
      <form action="" method="post">
        <p><input type="text" name="username">
        <p><input type="submit" value="Login">
      </form>
    '''

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))
