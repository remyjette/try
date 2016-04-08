from autograder import app, db
import json
import os
import requests
import random

class Course(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), unique = True)
  description = db.Column(db.String(200))
  student_list = db.Column(db.PickleType)

  def __init__(self, name, description):
    self.name = name
    self.description = description
    self.student_list = []

  def can_access(self, username):
    return self.can_modify(username) or username in self.student_list

  #TODO: Instructor/admin list
  def can_modify(self, username):
    return username == "rcj57"

class Assignment(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), unique = True)
  description = db.Column(db.String(200))
  is_open = db.Column(db.Boolean)
  course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
  course = db.relationship("Course", backref=db.backref("assignments", lazy="dynamic"))
  release_filename = db.Column(db.String(64))

  def __init__(self, name, description, course):
    self.name = name
    self.description = description
    self.course = course

  @property
  def directory_name(self):
    return self.course.name + "_" + self.name

  @property
  def testfile_dir(self):
    return os.path.join(app.config["TESTFILE_DIR"], self.directory_name)

  @property
  def release_code_dir(self):
    return os.path.join(app.config["RELEASECODE_DIR"], self.directory_name)

  @property
  def release_code_file(self):
    return os.path.join(self.release_code_dir, self.release_filename) if self.release_filename else None

class Testfile(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  filename = db.Column(db.String(255), unique = True)
  assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"))
  assignment = db.relationship("Assignment", backref=db.backref("testfiles", lazy="dynamic"))

  def __init__(self, filename, assignment):
    self.filename = filename
    self.assignment = assignment

  def grade(self, submission_file):
    test_code = open(self.filename, 'rb')
    release_code = open(self.assignment.release_code_file, 'rb')
    submission = open(submission_file, 'rb')

    docker_server = random.choice(app.config['OCAML_GRADER_SERVERS'])

    files = {'test_file': test_code}

    if submission is not None:
      files['submission'] = submission
    if release_code is not None:
      files['release'] = release_code

    r = requests.post(docker_server, files=files)

    results = json.loads(r.text)

    def public_results(results):
      for result in results:
        if result["name"] == "NO COMPILE":
          yield result
          continue
        unittest = self.unittests.filter_by(name=result["name"]).first()
        result["name"] = unittest.friendly_name
        if unittest.is_public:
          yield result

    return list(public_results(results))

  @property
  def path(self):
    return os.path.join(self.assignment.testfile_dir, self.filename)

class Unittest(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(255))
  friendly_name = db.Column(db.String(255))
  weight = db.Column(db.Float)
  is_public = db.Column(db.Boolean)
  testfile_id = db.Column(db.Integer, db.ForeignKey("testfile.id"))
  testfile = db.relationship("Testfile", backref=db.backref("unittests", lazy="dynamic"))

  def __init__(self, name, testfile):
    self.name = name
    self.friendly_name = name
    self.testfile = testfile
    self.public = False
    self.weight = 1
