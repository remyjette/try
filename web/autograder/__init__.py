#!/usr/bin/env python3

# TODO:

# Multiple input boxes for student upload (backend is already there!)
# Restrict student upload filetypes
# Make another module or two (PyUnit, JUnit?)
# Allow download / upload of test weights
# catch sql add errors and show nice messages (unique constraints?)
# handle testfile no tests on upload or gradeall
# handle grader error on upload/gradealll
# Grade all results - show test pass rates
# Grade all results - show NetID of no-compile / timeout
# Grade all results - tie CSV to session maybe? delete CSV at some point
# Documentation

# WOULD BE NICE:
# Add some sort of progress indicator to the 'Grade All' functionality

from flask import Flask, request, flash, get_flashed_messages, session
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

    if request.files and self.config['ERROR_FILES_DIR']:
      # Also log the submission so we can see what happened
      os.makedirs(self.config['ERROR_FILES_DIR'], exist_ok=True)
      time = datetime.datetime.now().isoformat()
      for f in request.files.values():
        filepath = os.path.join(
            self.config['ERROR_FILES_DIR'],
            time + "." + secure_filename(f.filename)
        )
        f.seek(0)
        f.save(filepath)

app = AutograderFlask(__name__)
app.config.from_object({
    "SSL_VERIFY": True,
    "ADMINS": [],
    "ERROR_LOG_EMAILS": [],
    "ERROR_LOG": None,
    "ERROR_FILES_DIR": None
})
app.config.from_pyfile('../config.cfg')
required_config_params = [
    "SECRET_KEY",
    "GRADER_SERVERS",
    "SQLALCHEMY_DATABASE_URI",
    "RELEASECODE_DIR",
    "TESTFILE_DIR",
    "GRADES_DIR"
]
missing_configs = set(required_config_params).difference(app.config.keys())
if missing_configs:
  raise Exception("The following config settings are missing: " + ", ".join(missing_configs))

app.config["TESTFILE_DIR"] = os.path.abspath(app.config["TESTFILE_DIR"])
app.config["RELEASECODE_DIR"] = os.path.abspath(app.config["RELEASECODE_DIR"])
app.config["GRADES_DIR"] = os.path.abspath(app.config["GRADES_DIR"])
app.config["ERROR_LOG"] = os.path.abspath(app.config["ERROR_LOG"])
app.config["ERROR_FILES_DIR"] = os.path.abspath(app.config["ERROR_FILES_DIR"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from autograder.main_views import main
from autograder.admin_views import admin
app.register_blueprint(main)
app.register_blueprint(admin, url_prefix='/admin')

@app.before_request
def before_request():
  try:
    request.username = request.headers["Remote-User"]
    request.global_admin = request.username in app.config["ADMINS"]
  except KeyError as e:
    if not app.debug:
      raise
  if app.debug:
    request.username = "debug"
    request.global_admin = True
    # flash a warning message if we're in admin in debug mode
    # try to avoid flashing the warning if it's already been flashed
    # this can happen (for example) on redirects or ajax requests as the
    # flash message isn't consumed
    flashes = session.get('_flashes', [])
    if ('warning', 'DEBUG mode is enabled!') not in flashes:
      flash("DEBUG mode is enabled!", "warning")


if not app.debug and app.config["ERROR_LOG"]:
  import logging
  file_handler = logging.FileHandler(app.config["ERROR_LOG"])
  file_handler.setLevel(logging.WARNING)
  file_handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s '
      '[in %(pathname)s:%(lineno)d]'
  ))
  app.logger.setLevel(logging.WARNING)
  app.logger.addHandler(file_handler)

if not app.debug and app.config['ADMINS']:
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


