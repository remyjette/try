#!/usr/bin/env python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

import autograder.secret_key

app.config['OCAML_GRADER_SERVERS'] = ['http://localhost:8000']

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



