from autograder import app, db
from flask import request
import json
import os
import requests
import random
import shutil
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
import types


class Course(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), unique = True, nullable = False)
  description = db.Column(db.String(200))
  instructors = db.Column(db.PickleType, nullable = False)
  students = db.Column(db.PickleType, nullable = False)
  default_timeout = db.Column(db.Integer, nullable = False)
  default_tester = db.Column(db.String(200))
  assignments=db.relationship("Assignment", backref="course", lazy="dynamic", cascade="all, delete-orphan")

  def __init__(self, name=None, description=None):
    self.name = name
    self.description = description
    self.students = []
    self.instructors = []

  def can_access(self, username):
    return self.can_modify(username) or username in self.students

  def can_modify(self, username):
    return request.global_admin or username in self.instructors

  @classmethod
  def accessible_by(cls, username):
    return [c for c in Course.query.all() if c.can_access(username)]

  @classmethod
  def modifiable_by(cls, username):
    return [c for c in Course.query.all() if c.can_modify(username)]

  def delete(self):
    for a in self.assignments.all():
      a.delete()
    db.session.delete(self)
    db.session.commit()


class Assignment(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), nullable = False)
  description = db.Column(db.String(200))
  visible = db.Column(db.Boolean, nullable = False)
  max_score = db.Column(db.Integer)
  problems = db.Column(db.PickleType)
  course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable = False)
  release_filename = db.Column(db.String(64))
  testfiles=db.relationship("Testfile", backref="assignment", lazy="dynamic", cascade="all, delete-orphan")
  __table_args__ = (db.UniqueConstraint('name', 'course_id'),)

  def __init__(self, course=None, name=None, visible=None):
    self.name = name
    self.course = course
    self.visible = visible

  @property
  def directory_name(self):
    return self.course.name + "_" + self.name

  @property
  def testfile_dir(self):
    return os.path.join(app.config["TESTFILE_DIR"], self.directory_name)

  @property
  def grades_dir(self):
    return os.path.join(app.config["GRADES_DIR"], self.directory_name)

  @property
  def release_code_dir(self):
    return os.path.join(app.config["RELEASECODE_DIR"], self.directory_name)

  @property
  def release_code_file(self):
    return os.path.join(self.release_code_dir, self.release_filename) if self.release_filename else None

  def delete(self):
    db.session.delete(self)
    db.session.commit()
    shutil.rmtree(self.release_code_dir, ignore_errors=True)
    shutil.rmtree(self.testfile_dir, ignore_errors=True)

class Testfile(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  filename = db.Column(db.String(255), nullable=False)
  tester = db.Column(db.String(200), nullable=False)
  required_files = db.Column(db.PickleType)
  timeout = db.Column(db.Integer, nullable=False)
  assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"), nullable=False)
  unittests=db.relationship("Unittest", backref="testfile", lazy="dynamic", cascade="all, delete-orphan")
  __table_args__ = (db.UniqueConstraint('filename', 'assignment_id'),)

  @property
  def path(self):
      return os.path.join(self.assignment.testfile_dir, self.filename)

  def __init__(self, filename, assignment, tester=None, timeout=None, required_files=None):
    self.filename = filename
    self.assignment = assignment
    self.tester = tester
    self.timeout = timeout
    self.required_files = required_files if required_files else []

  def to_dict(self):
    d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
    d["unittests"] = [u.to_dict() for u in self.unittests.all()]
    return d

  def delete(self):
    db.session.delete(self)
    db.session.commit()
    os.unlink(self.path)

  def grade(self, submission_files, public_only=True, check_required=True):
    test_code = open(self.path, 'rb')
    release_code = open(self.assignment.release_code_file, 'rb') if self.assignment.release_code_file else None
    testers = app.config['GRADER_SERVERS'][self.tester]
    tester_server = random.choice(testers)

    files = {'test_file': test_code}

    if submission_files is not None:
      i = 0
      for submission_file in submission_files:
        submission = open(submission_file, 'rb')
        if submission is not None:
          files['submission' + str(i)] = submission
          i += 1

    if release_code is not None:
      files['release'] = release_code

    data = {
      "required_files": self.required_files if check_required else [],
      "timeout": self.timeout
    }

    #TODO what if this fails on testupload or grade_all?
    r = requests.post(
      tester_server,
      data=data,
      files=files,
      verify=app.config["SSL_VERIFY"]
    )
    results = json.loads(r.text)

    # If the caller requested all results (including non-public results)
    # or if the result was an error, send everything back to the caller
    if not public_only or (results.get("error")):
      return results

    def public_results(results):
      for result in results:
        unittest = self.unittests.filter_by(name=result["name"]).first()
        result["name"] = unittest.friendly_name
        if unittest.is_public:
          yield result

    return {"results": list(public_results(results["results"]))}

  @property
  def path(self):
    return os.path.join(self.assignment.testfile_dir, self.filename)


class Unittest(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(255))
  friendly_name = db.Column(db.String(255))
  weight = db.Column(db.Float)
  is_public = db.Column(db.Boolean)
  problem = db.Column(db.String(255))
  testfile_id = db.Column(db.Integer, db.ForeignKey("testfile.id"))

  def __init__(self, name, testfile):
    self.name = name
    self.friendly_name = name
    self.testfile = testfile
    self.public = False
    self.weight = 1

  def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Log(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  netid = db.Column(db.String(20))
  tests_passed = db.Column(db.Integer)
  total_tests = db.Column(db.Integer)
  results = db.Column(db.String())
  timestamp = db.Column(db.DateTime())

  def __init__(self, netid, tests_passed, total_tests, results):
    self.netid = netid
    self.tests_passed = tests_passed
    self.total_tests = total_tests
    self.results = results
    self.timestamp = datetime.now()
