from autograder import app, db
from autograder.models import Course, Assignment, Testfile, Unittest
from autograder.admin_forms import CourseForm, AssignmentForm, NewTestFileForm, TestFileForm, UnitTestForm
from flask import render_template, request, abort, send_file, flash, Blueprint, redirect, url_for, jsonify, g
from autograder.grade_assignment import grade_assignment
from werkzeug import secure_filename
from sqlalchemy.orm.exc import NoResultFound
import os
import json
import uuid
import shutil

admin = Blueprint('admin', __name__)


@admin.before_request
def before_request():
  if request.global_admin:
    g.courses = Course.query.all()
  else:
    g.courses = Course.accessible_by(request.username)
    if not g.courses:
      return abort(403)


@admin.context_processor
def context_processor():
  return dict(courses=g.courses)


@admin.route("/")
def index():
  return render_template("admin_landing.html")


@admin.route("/new/", methods=["GET", "POST"], endpoint="new_course")
@admin.route("/<course_name>/", methods=["GET", "POST"])
def course(course_name=None):
  if course_name is None:
    if not request.global_admin:
      # Only allow global admins to create new courses
      return abort(403)
    course = None
    form = CourseForm()
  else:
    course = Course.query.filter_by(name=course_name).first()
    if course is None:
      return abort(404)
    if not course.can_modify(request.username):
      return abort(403)
    form = CourseForm(obj=course)

  if form.is_submitted():
    if form.delete.data:
      course.delete()
      return redirect(url_for('.index'))

    error = False
    if course is None or course.name != form.name.data:
      if form.name.data is None or form.name.data in ["", "new", "admin"]:
        flash("Invalid New Course Name", "error")
        error = True
      elif Course.query.filter_by(name=form.name.data).count():
        flash("Course '" + form.name.data + "' already exists.", "error")
        error = True

    if not error:
      def get_stripped_username_list(l):
        return [username.strip() for username in l.replace("@cornell.edu", "").replace("\n", ",").split(",") if username.strip()]
      form.instructors.data = get_stripped_username_list(form.instructors.data)
      form.students.data = get_stripped_username_list(form.students.data)
      if course is None:
        course = Course()
        db.session.add(course)
      form.populate_obj(course)
      db.session.commit()
      if course.name != course_name:
        #the course name was changed. redirect to the new course
        #This will also redirect a new course
        return redirect(url_for(".course", course_name=course.name))

  if (course):
    form.instructors.data = "\n".join(course.instructors)
    form.students.data = "\n".join(course.students)

  return render_template("admin_course.html", form=form, course=course)


@admin.route("/<course_name>/new/", methods=["GET", "POST"], endpoint="new_assignment")
@admin.route("/<course_name>/<assignment_name>/", methods=["GET", "POST"])
def assignment(course_name, assignment_name=None):
  try:
    course = Course.query.filter_by(name=course_name).one()
    if assignment_name is None:
      assignment = None
      form = AssignmentForm()
    else:
      assignment = course.assignments.filter_by(name=assignment_name).one()
      form = AssignmentForm(obj=assignment)
  except NoResultFound:
    return abort(404)
  if not course.can_modify(request.username):
    return abort(403)

  #add a blank entry to use as default
  form.problems.append_entry()

  if form.is_submitted():
    if form.delete.data:
      assignment.delete()
      return redirect(url_for('.course', course_name=course.name))

    error = False
    if assignment is None or assignment.name != form.name.data:
      if form.name.data is None or form.name.data in ["", "new"]:
        flash("Invalid New Assignment Name", "error")
        error = True
      elif course.assignments.filter_by(name=form.name.data).count():
        flash("Assignment '" + form.name.data + "' already exists.", "error")
        error = True

    if not error:
      if assignment is None:
        is_new = True
        assignment = Assignment(course=course)
        db.session.add(assignment)
      form.populate_obj(assignment)
      assignment.problems = [p for p in assignment.problems if p.problem_name and p.score]
      if form.release_file.data:
        try:
          if (assignment.release_code_file):
            os.unlink(assignment.release_code_file)
          else:
            os.makedirs(assignment.release_code_dir, exist_ok=True)
          f = form.release_file.data
          assignment.release_filename = secure_filename(f.filename)
          f.save(assignment.release_code_file)
          db.session.commit()
        except GeneratorExit:
          error = True
          db.session.rollback()
          if is_new:
            assignment = None
          flash("Could not save the release file.", "error")
      else:
        db.session.commit()
      if not error:
        return redirect(url_for(".assignment", course_name=course.name, assignment_name=assignment.name))

  if assignment and assignment.testfiles.filter(Testfile.unittests.any(Unittest.is_public)).count() == 0 and assignment.visible:
    flash("Assignment '" + assignment.name + "' is marked 'visible' but there"
          " are no public test files. To avoid confusion this assignment will"
          " be hidden from students despite the visibility setting.", "warning")

  testfiles_json = json.dumps([t.to_dict() for t in assignment.testfiles.all()]) if assignment else None

  other_forms = {
    "new_testfile_form": NewTestFileForm(),
    "testfile_form": TestFileForm(),
    "unittest_form": UnitTestForm()
  }
  if assignment:
    other_forms["new_testfile_form"].tester.default = course.default_tester
    other_forms["new_testfile_form"].timeout.default = course.default_timeout
    other_forms["new_testfile_form"].process()
    other_forms["unittest_form"].problem.choices = [('', '')] + [(x.problem_name, x.problem_name) for x in assignment.problems]

  return render_template(
    "admin_assignment.html",
    form=form,
    other_forms=other_forms,
    course=course,
    assignment=assignment,
    testfiles_json = testfiles_json
  )


@admin.route("/<course_name>/<assignment_name>/testfile/", methods=["PUT"])
@admin.route("/<course_name>/<assignment_name>/testfile/<int:testfile_id>/", methods=["POST", "DELETE"])
def testfile(course_name, assignment_name, testfile_id=None):
  try:
    course = Course.query.filter_by(name=course_name).one()
    assignment = course.assignments.filter_by(name=assignment_name).one()
  except NoResultFound:
    return abort(404)
  if not course.can_modify(request.username):
    return abort(403)

  # TODO error handling, overwrite
  if request.method == "PUT":
    f = request.files['test_file']
    filename = secure_filename(f.filename)
    testfile_dir = assignment.testfile_dir
    os.makedirs(testfile_dir, exist_ok=True)
    f.save(os.path.join(testfile_dir, filename))
    required_files = [r.strip() for r in request.form["required_files"].split("\n") if r.strip()]

    testfile = Testfile(filename, assignment, request.form["tester"], request.form["timeout"], required_files)

    # TODO handle failure of testfile.grade (exceptions)
    # TODO handle no unit tests
    # TODO handle no compile or other error
    release_code_response = testfile.grade(
      None,
      check_required=False,
      public_only=False
    )

    print(release_code_response)

    test_names = [result["name"] for result in release_code_response["results"]]
    for test_name in test_names:
      unittest = Unittest(test_name, testfile)
      db.session.add(unittest)

    db.session.add(testfile)
    db.session.commit()
    return jsonify(testfile.to_dict())

  elif request.method == "POST":
    try:
      testfile = assignment.testfiles.filter_by(id=testfile_id).one()
    except NoResultFound:
      return abort(404)

    data = request.get_json()
    testfile.required_files = [r.strip() for r in data["required_files"] if r.strip()]
    testfile.timeout = data["timeout"]
    for test in testfile.unittests.all():
      test_data = [x for x in data["unittests"] if x["id"] == test.id][0]
      test.friendly_name = test_data["friendly_name"]
      test.is_public = test_data["is_public"]
      test.weight = test_data["weight"]
      test.problem = test_data["problem"]

    db.session.commit()

    return "Save Successful"

  elif request.method == "DELETE":
    try:
      testfile = assignment.testfiles.filter_by(id=testfile_id).one()
    except NoResultFound:
      return abort(404)
    testfile.delete()

    return "Test file deleted"


@admin.route("/<course_name>/<assignment_name>/grade/", methods=["POST"])
def grade_submissions(course_name, assignment_name):
  try:
    course = Course.query.filter_by(name=course_name).one()
    assignment = course.assignments.filter_by(name=assignment_name).one()
  except NoResultFound:
    return abort(404)
  if not course.can_modify(request.username):
    return abort(403)

  submissions_archive = request.files['submissions']

  csv_id= str(uuid.uuid4())
  csvfile, final_results = grade_assignment(assignment, submissions_archive)
  os.makedirs(assignment.grades_dir, exist_ok=True)
  shutil.copy(csvfile.name, os.path.join(assignment.grades_dir, csv_id))
  csvfile.close()

  grade_response = {'csv_id': csv_id, 'results': final_results}
  if assignment.problems:
    grade_response["problems_max"] = {p.problem_name: p.score for p in assignment.problems}
    grade_response["max_score"] = sum(p.score for p in assignment.problems)
  else:
    grade_response["max_score"] = assignment.max_score
  return jsonify(grade_response)

@admin.route("/<course_name>/<assignment_name>/grade/<csv_id>/")
def get_grades_csv(course_name, assignment_name, csv_id):
  try:
    course = Course.query.filter_by(name=course_name).one()
    assignment = course.assignments.filter_by(name=assignment_name).one()
  except NoResultFound:
    return abort(404)
  if not course.can_modify(request.username):
    return abort(403)

  csv_filename = course.name + "_" + assignment.name + "_grades.csv"
  try:
    return send_file(
      os.path.join(assignment.grades_dir, csv_id),
      mimetype="text/csv",
      as_attachment=True,
      attachment_filename=csv_filename
    )
  except FileNotFoundError:
    return abort(404)
