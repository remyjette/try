#!/usr/bin/env python3



#TODOS:
#Finish CSV so the output is _fully_ CMS-compatible
# : Actually use the weights

#auditing - make logs

#Flesh out admin - allow other instructors to edit course, allow other admins

#Allow deletion of testfiles / assignments / courses

#Allow replacing release files

#Multiple input boxes for student upload (backend is already there!)

#STYLING

#Give reports (average scores and stuff) after grading all submissions

#Ajax-ify 'the all submissions', maybe make it have a progress bar?



#Make another module or two (PyUnit, JUnit?)

#DEPLOY !!!

#Config file instead of configuration in __init__.py

#Make some things configurable by course (such as container timeouts)

#Allow download / upload of test weights


from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
import datetime
import os
import textwrap

class AutograderFlask(Flask):
  def log_exception(self, exc_info):
    if hasattr(request, 'username'):
      user = request.username
    else:
      user = "<unknown>"
    self.logger.error(textwrap.dedent("""\
      Request:   {method} {path}
      User:      {user}
      Agent:     {agent_platform} | {agent_browser} {agent_browser_version}
      Raw Agent: {agent}
      """).format(
          method = request.method,
          path = request.path,
          ip = request.remote_addr,
          agent_platform = request.user_agent.platform,
          agent_browser = request.user_agent.browser,
          agent_browser_version = request.user_agent.version,
          agent = request.user_agent.string,
          user=user
      ), exc_info=exc_info
    )

    if (request.files):
      # Also log the submission so we can see what happened
      os.makedirs("error_log", exist_ok=True)
      time = datetime.datetime.now().isoformat()
      i = 0
      for f in request.files.values():
        f.save(os.path.join("error_log", time + "." + secure_filename(f.filename)))

app = AutograderFlask(__name__)

import autograder.secret_key

app.config['OCAML_GRADER_SERVERS'] = ['https://cs3110.remyjette.com:8000']
app.config["ADMINS"] = ["rcj57@cornell.edu"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath("autograder.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["TESTFILE_DIR"] = os.path.abspath("test_files")
app.config["RELEASECODE_DIR"] = os.path.abspath("release_code")
db = SQLAlchemy(app)

import autograder.views

@app.before_request
def before_request():
  try:
    request.username = request.headers["Remote-User"]
  except KeyError as e:
    if not app.debug:
      app.logger.error(e)
      raise
  if app.debug:
    request.username = "debug"

if not app.debug:
  import logging
  file_handler = logging.FileHandler("error.log")
  file_handler.setLevel(logging.WARNING)
  file_handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s '
      '[in %(pathname)s:%(lineno)d]'
  ))
  app.logger.setLevel(logging.WARNING)
  app.logger.addHandler(file_handler)

if not app.debug:
  import logging
  from logging.handlers import SMTPHandler

  mail_handler = SMTPHandler('127.0.0.1',
                             'autograder@try.cs.cornell.edu',
                             app.config["ADMINS"],
                             'ERROR in Autograder Application')

  mail_handler.setFormatter(logging.Formatter(textwrap.dedent("""\
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    """)))

  mail_handler.setLevel(logging.ERROR)
  app.logger.addHandler(mail_handler)


