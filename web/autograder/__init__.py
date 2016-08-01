"""This package creates the web-based frontend for the autograder system.

Admin pages allow admins/instructors to create and manage courses, assignments,
test files, and unit tests. It also allows them to upload an archive of
student submissions and have each submission graded.

The student-facing pages allow students to upload their code and get feedback
on test passes/failures.

This __init__ file sets up the Flask application object in the variable app
and the Flask_SQLAlchemy database connection in the variable db.

The flask application is configured using config.cfg.
"""

#!/usr/bin/env python3

from flask import Flask, request, flash, get_flashed_messages, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename
import datetime
import os
import textwrap

class AutograderFlask(Flask):
  """A custom subclass of 'Flask' to override log_exception()"""
  def log_exception(self, exc_info):
    """Overwride to provide additional information in the error log

    In addition to storing information such as the requesting user and the
    path requested, this will also store any submitted files if the config
    ERROR_FILES_DIR is set."""
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

# Instatiate the flask object here so other modules can access it as
# autograder.app
app = AutograderFlask(__name__)
# Default config options - set these first, and if provided by the config file
# they will be overridden.
app.config.from_object({
    "SSL_VERIFY": True,
    "ADMINS": [],
    "ERROR_LOG_EMAILS": [],
    "ERROR_LOG": None,
    "ERROR_FILES_DIR": None
})
# Load config options from config.cfg
app.config.from_pyfile('../config.cfg')
# A list of required config options (the system won't work without them).
# Check if any are missing - if any are, throw an exception because we can't
# initialize this package
required_config_params = [
    "SECRET_KEY",
    "GRADER_SERVERS",
    "SQLALCHEMY_DATABASE_URI",
    "RELEASECODE_DIR",
    "TESTFILE_DIR",
    "GRADES_DIR"
]
_missing_configs = set(required_config_params).difference(app.config.keys())
if _missing_configs:
  raise Exception(
    "The following config settings are missing: " + ", ".join(_missing_configs)
  )

# If any of the _DIR configs are relative paths, make them absolute paths so
# we don't have to worry about any mixups from different modules reading the
# path
app.config["TESTFILE_DIR"] = os.path.abspath(app.config["TESTFILE_DIR"])
app.config["RELEASECODE_DIR"] = os.path.abspath(app.config["RELEASECODE_DIR"])
app.config["GRADES_DIR"] = os.path.abspath(app.config["GRADES_DIR"])
app.config["ERROR_LOG"] = os.path.abspath(app.config["ERROR_LOG"])
app.config["ERROR_FILES_DIR"] = os.path.abspath(app.config["ERROR_FILES_DIR"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Now that app is created, pull in our views.
from autograder.main_views import main
from autograder.admin_views import admin
app.register_blueprint(main)
app.register_blueprint(admin, url_prefix='/admin')

@app.before_request
def _before_request():
  """Before every request, set request.username and perform other actions

  This application expects that the user is already authenticated by some sort
  of external service and that the requester's username will be in the request
  headers. To make it easier to access, we store the username in
  request.username.

  In addition to getting the username, we also set the request.global_admin flag
  if the user is in that list in the config. Lastly, if we are in debug mode
  we set the request username to "debug" instead and flash a warning."""
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
    if ('warning', 'DEBUG mode is enabled!') not in session.get('_flashes', []):
      flash("DEBUG mode is enabled!", "warning")


# If the ERROR_LOG config is set, create a FileHandler logger to log WARNING
# or higher.
if not app.debug and app.config["ERROR_LOG"]:
  import logging
  _file_handler = logging.FileHandler(app.config["ERROR_LOG"])
  _file_handler.setLevel(logging.WARNING)
  _file_handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)s: %(message)s '
      '[in %(pathname)s:%(lineno)d]'
  ))
  app.logger.addHandler(_file_handler)

# If the ERROR_LOG_EMAILS config is set, create a SMTPHandler logger to send
# an email for ERROR or higher
if not app.debug and app.config['ERROR_LOG_EMAILS']:
  import logging
  from logging.handlers import SMTPHandler

  _mail_handler = SMTPHandler('127.0.0.1',
                             'autograder@try.cs.cornell.edu',
                             app.config["ERROR_LOG_EMAILS"],
                             'ERROR in Autograder Application')

  _mail_handler.setFormatter(logging.Formatter(textwrap.dedent("""\
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    """)))

  _mail_handler.setLevel(logging.ERROR)
  app.logger.addHandler(_mail_handler)


