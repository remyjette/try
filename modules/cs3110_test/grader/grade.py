#!/usr/bin/env python3

from flask import Flask, request
from util import cd, save_or_extract
from werkzeug import secure_filename
import tempfile
import shutil

app = Flask(__name__)

@app.route("/", methods=["POST"])
def grade():
  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):
      submission = request.files['submission']
      release = request.files['release']
      t = request.files['test_file']

      save_or_extract(release, tempdir)
      save_or_extract(submission, tempdir)
      test_filename = secure_filename(t.filename)
      test_file = open(os.path.join(tempdir, test_filename), "w")
      t.save(test_file)
      shutil.copyfileobj(open("paounit_json_response.ml", r), test_file)
      test_file.close()

      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + test_filename), stdout = subprocess.PIPE)
      if compiler.returncode != 0:
        return [{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}]
      tester = subprocess.run(shlex.split("cs3110 test " + test_filename), stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
      return json.loads(tester.stdout.decode("utf-8"))

if __name__ == "__main__":
  app.run(host="::", port=8000, threaded=True)
