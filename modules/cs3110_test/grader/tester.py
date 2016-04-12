#!/usr/bin/env python3

from flask import Flask, request
from util import cd, save_or_extract
from distutils.dir_util import copy_tree
from werkzeug import secure_filename
import tempfile
import shutil
import os
import shlex
import shutil
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

      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + test_filename), stdout = subprocess.PIPE)
      if compiler.returncode != 0:
        return json.dumps([{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}])
      tester = subprocess.run(shlex.split("cs3110 test " + test_filename), stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
      return tester.stdout.decode("utf-8")

if __name__ == "__main__":
  app.debug = True
  use_debugger = True

  app.run(host="::", port=8000, threaded=True)
