#!/usr/bin/env python3

from flask import Flask, request
from distutils.dir_util import copy_tree
from werkzeug import secure_filename
from contextlib import contextmanager
import zipfile
import os
import shlex
import subprocess
import tempfile
import json

app = Flask(__name__)

paounit_json_response = open("paounit_json_response.ml", "rb").readlines()

@app.route("/", methods=["POST"])
def tester():
  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):

      required_files = request.form.getlist("required_files")

      if 'release' in request.files:
        release = request.files['release']
        save_or_extract(release, tempdir)

      i = 0
      while 'submission' + str(i) in request.files:
        submission = request.files['submission' + str(i)]
        submitted_files = save_or_extract(submission, tempdir)
        required_files = filter(lambda f: f not in submitted_files, required_files)
        i += 1
      required_files = list(required_files)

      if required_files:
        return json.dumps([{
          'name': 'NO COMPILE',
          'passed': False,
          'message': "Missing required files:\n\n" + "\n".join(required_files)
        }])

      t = request.files['test_file']
      test_filename = secure_filename(t.filename)
      test_file = open(os.path.join(tempdir, test_filename), "wb")
      t.save(test_file)
      test_file.writelines(paounit_json_response)
      test_file.close()

      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + test_filename), stdout=subprocess.PIPE)
      if compiler.returncode != 0:
        return json.dumps([{'name': 'NO COMPILE', 'passed': False, "message": compiler.stdout.decode("utf-8")}])
      try:
        tester = subprocess.run(shlex.split("cs3110 test " + test_filename), timeout=60, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      except subprocess.TimeoutExpired:
        return json.dumps([{'name': 'TIMEOUT EXPIRED', 'passed': False, "message": "The timeout has expired."}])
      with open("test-results.json", "r") as results:
        return results.read()


@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def get_file_extension(filename):
  try:
    return filename.rsplit('.', 1)[1]
  except IndexError:
    return None

def save_or_extract(file, target):
  if get_file_extension(file.filename) == "zip":
    archive = zipfile.ZipFile(file)
    archive.extractall(target)
    return archive.namelist()
  else:
    filename = secure_filename(file.filename)
    file.save(os.path.join(target, filename))
    return [filename]


if __name__ == "__main__":
  app.debug = True
  use_debugger = True

  app.run(host="::", port=8000, threaded=True)
