from autograder import app, db
import os

class Course(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), unique = True)
  description = db.Column(db.String(200))

  def __init__(self, name, description):
    self.name = name
    self.description = description


class Assignment(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20), unique = True)
  description = db.Column(db.String(200))
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
  def release_code_file(self):
    return os.path.join(app.config["RELEASECODE_DIR"], self.release_code_dir, self.release_file_name)

class Testfile(db.Model):
  id = db.Column(db.Integer, primary_key = True)
  filename = db.Column(db.String(255), unique = True)
  assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"))
  assignment = db.relationship("Assignment", backref=db.backref("testfiles", lazy="dynamic"))

  def __init__(self, filename, assignment):
    self.filename = filename
    self.assignment = assignment

  @property
  def path(self):
    return os.path.join(self.assignment.testfile_dir, self.filename)

