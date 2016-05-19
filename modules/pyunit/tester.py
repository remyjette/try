#!/usr/bin/env python3.5

from flask import Flask, request, jsonify
from werkzeug import secure_filename
from contextlib import contextmanager
import zipfile
import tempfile
import json
import os
import unittest
import traceback
import sys
import importlib.util

def run_tests(filename):
    class TestResultWithSuccesses(unittest.TestResult):
        def __init__(self):
            unittest.TestResult.__init__(self)
            self.successes = []

        def addFailure(self, test, err):
            "Called when a failure has occurred"
            self.failures.append((test, err))

        def addSuccess(self, test):
            "Called when a test has completed successfully"
            self.successes.append(test)

    class TestRunner:
        def run(self, test):
            "Run the given test case or test suite."
            result = TestResultWithSuccesses()
            test(result)

            return result

    old_path = sys.path
    sys.path = [os.getcwd()]
    try:
        spec = importlib.util.spec_from_file_location("", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        message = traceback.format_exc(5)
        return {'error': 'ERROR LOADING MODULE', 'message': message}
    harness = unittest.main(module=module, testRunner=TestRunner(), exit=False)
    sys.path = old_path

    result_list = [{
            'name': test.id(),
            'passed': True,
            'message': None
            } for test in harness.result.successes] + \
            [{
            'name': test.id(),
            'passed': False,
            'message': str(err)
            } for test, (cls, err, tb) in (harness.result.failures)] + \
            [{
            'name': test.id(),
            'passed': False,
            'message': str(err)
            } for test, err in (harness.result.errors)]

    return {'results': result_list}

app = Flask(__name__)

@app.route("/", methods=["POST"])
def tester():
  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):

      required_files = request.form.getlist("required_files")

      if 'release' in request.files:
        release = request.files['release']
        save_or_extract(release, tempdir)

      i = 0
      try:
        while 'submission' + str(i) in request.files:
          submission = request.files['submission' + str(i)]
          submitted_files = save_or_extract(submission, tempdir)
          required_files = filter(lambda f: f not in submitted_files, required_files)
          i += 1
      except zipfile.BadZipFile as e:
        return json.dumps({'error': 'UPLOAD ERROR', "message": "Uploaded .zip file is invalid."})
      required_files = list(required_files)

      if required_files:
        return json.dumps({
          'error': 'MISSING REQUIRED FILES',
          'message': "Missing required files:\n\n" + "\n".join(required_files)
        })

      t = request.files['test_file']
      test_filename = secure_filename(t.filename)
      t.save(os.path.join(tempdir, test_filename))

      results = run_tests(test_filename)
      return json.dumps(results)

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
  app.run(host="::", port=9000, threaded=True)
