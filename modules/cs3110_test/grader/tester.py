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
      if 'release' in request.files:
        release = request.files['release']
        save_or_extract(release, tempdir)

      i = 0
      while 'submission' + str(i) in request.files:
        submission = request.files['submission' + str(i)]
        save_or_extract(submission, tempdir)
        i += 1

      t = request.files['test_file']
      test_filename = secure_filename(t.filename)
      test_file = open(os.path.join(tempdir, test_filename), "wb")
      t.save(test_file)
      test_file.writelines(paounit_json_response)
      test_file.close()

      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + test_filename), stdout=subprocess.PIPE)
      if compiler.returncode != 0:
        return json.dumps([{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}])
      try:
        tester = subprocess.run(shlex.split("cs3110 test " + test_filename), timeout=60, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      except subprocess.TimeoutExpired:
        return json.dumps([{'name': 'TIMEOUT EXPIRED', 'failed': True, "message": "The timeout has expired."}])
      return tester.stdout.decode("utf-8")


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
    release_archive = zipfile.ZipFile(file)
    release_archive.extractall(target)
  else:
    file.save(os.path.join(target, secure_filename(file.filename)))


if __name__ == "__main__":
  app.debug = True
  use_debugger = True

  app.run(host="::", port=8000, threaded=True)
