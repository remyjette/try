#!/usr/bin/env python3

from flask import Flask, request, jsonify
from distutils.dir_util import copy_tree
from werkzeug import secure_filename
from contextlib import contextmanager
import zipfile
import os
import shlex
import subprocess
import tempfile
import json
import psutil

app = Flask(__name__)

paounit_json_response = open("paounit_json_response.ml", "rb").readlines()

@app.route("/", methods=["POST"])
def tester():
  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):
      # The timeout *should* be provided, but we give a resonable default just
      # in case it isn't.
      timeout = request.form.get("timeout", default=60, type=int)

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
        return json.dumps({'error': 'NO COMPILE', "message": "Uploaded .zip file is invalid."})
      required_files = list(required_files)

      if required_files:
        return json.dumps({
          'error': 'NO COMPILE',
          'message': "Missing required files:\n\n" + "\n".join(required_files)
        })

      t = request.files['test_file']
      test_filename = secure_filename(t.filename)
      test_file = open(os.path.join(tempdir, test_filename), "wb")
      t.save(test_file)
      test_file.writelines(paounit_json_response)
      test_file.close()

      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson,str " + test_filename), stdout=subprocess.PIPE)
      if compiler.returncode != 0:
        return json.dumps({'error': 'NO COMPILE', "message": compiler.stdout.decode("utf-8")})
      # Now that the code is compiled, remove the test file source as it's not
      # needed to prevent student code from easily reading it.
      os.remove(os.path.join(tempdir, test_filename))
      os.remove(os.path.join(tempdir, "_build", test_filename))
      try:
        tester = subprocess.Popen(shlex.split("cs3110 test " + test_filename), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tester.wait(timeout=timeout)
      except subprocess.TimeoutExpired:
        parent = psutil.Process(tester.pid)
        children = parent.children(recursive=True)
        for child in children:
          child.kill()
        parent.kill()
        return json.dumps({'error': 'TIMEOUT EXPIRED', "message": "The timeout has expired."})
      with open("test-results.json", "r") as results:
        return json.dumps({'results': json.load(results)})


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

  app.run(host="::", port=8888, threaded=True)
