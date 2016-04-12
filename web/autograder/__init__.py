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


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

import autograder.secret_key

app.config['OCAML_GRADER_SERVERS'] = ['https://cs3110.remyjette.com:8000']

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath("autograder.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["TESTFILE_DIR"] = os.path.abspath("test_files")
app.config["RELEASECODE_DIR"] = os.path.abspath("release_code")
db = SQLAlchemy(app)

import autograder.views

if __name__ == "__main__":
  app.debug = True
  use_debugger = True

  app.run(host="::")



