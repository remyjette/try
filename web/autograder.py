#!/usr/bin/env python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from views import views
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///autograder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["TESTFILE_DIR"] = os.path.abspath("test_files")
app.config["RELEASECODE_DIR"] = os.path.abspath("release_code")
db = SQLAlchemy(app)

app.register_blueprint(views)

if __name__ == "__main__":
  app.debug = True
  use_debugger = True

  app.run(host="::")



