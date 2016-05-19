from autograder import app
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SelectField, FieldList, DecimalField, SubmitField, FormField
from wtforms.widgets import ListWidget, html_params
from collections import namedtuple
from types import SimpleNamespace

tester_choices = sorted([(x, x) for x in app.config["GRADER_SERVERS"].keys()])

class CourseForm(Form):
  name = StringField('Course Name')
  visible = BooleanField('Visible to Students')
  instructors = TextAreaField('Instructors')
  students = TextAreaField('Students')
  default_timeout = IntegerField('Default Timeout for New Test Files', default=10)
  default_tester = SelectField('Default Testing Engine', choices=tester_choices)
  submit = SubmitField("Save")
  delete = SubmitField("Delete")


class ProblemFormField(Form):
  problem_name = StringField()
  score = IntegerField()


def problem_field_widget(field, ul_class='', **kwargs):
  field_id = kwargs.pop('id', field.id)
  html = ["<ul %s>" % html_params(id=field_id, class_=ul_class)]
  for entry in field.entries:
    html.append("<li>" + "Name: " + entry.form.problem_name() + " Max Score: " + entry.form.score() + "</li>")
  html.append("</ul>")
  return ''.join(html)


class AssignmentForm(Form):
  name = StringField('Assignment Name')
  visible = BooleanField('Visible to Students')
  release_file = FileField('Release Code')
  max_score = IntegerField('Max Score')
  problems = FieldList(FormField(ProblemFormField, default=lambda: SimpleNamespace()), min_entries=0, widget=problem_field_widget)
  submit = SubmitField("Save")
  delete = SubmitField("Delete")


class NewTestFileForm(Form):
  test_file = FileField('File')
  tester = SelectField('Testing Engine', choices=tester_choices)
  timeout = IntegerField('Timeout')
  required_files = TextAreaField('Required Files')

# TestFileForm and UnitTestForm will be cloned and repeated on the page.
# The id attribute would be problematic as we don't want multiple DOM elements
# with the same id, so we clear them
def clear_id(field):
  field.id = ""
  field.label.field_id = ""

class TestFileForm(Form):
  required_files = TextAreaField('Required Files')
  timeout = IntegerField('Timeout')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for f in self:
      clear_id(f)

class UnitTestForm(Form):
  friendly_name = StringField('Test Name')
  weight = DecimalField('Weight', places=2)
  is_public = BooleanField('Public Test')
  problem = SelectField('Problem')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for f in self:
      clear_id(f)
