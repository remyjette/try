"""This file creates a very basic flask application that provides a single
endpoint to accept grade requests and return JSON results.

"""

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
  """Endpoint to accept grade requests.

  Expects the following POST parameters:

  required_files - Optional. A list of files that must be present in the
    submission. Allows us to return a better error message to accompany the no
    compile mthan what would be returned if we just compiled against the release
    code. If not provided, this check will be skipped.

  release - Optional. The release code. If it is a .zip archive, it'll be
    extracted. If not provided, the test file will be compiled against the
    student code with no additional files.

  submission# - Optional. a submitted file or .zip archive. Any files present
    will replace release code files. Multiple files can be included, the POST
    keys should be submission0, submission1, ..., submissionN. If not provided,
    the test file will be compiled against the release code (for example to get
    a list of the unit test names).

  test_file - The file containing unit tests to compile with the given code.

  timeout - Optional. How long (in seconds) to allow for a single grade request.
    If exceeded, an error will be returned. Defaults to 60.
  """
  # First thing we do on every request is create a temporary directory and cd
  # into it. That way, everything gets wiped when the request ends.
  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):
      # The timeout *should* be provided, but we give a resonable default just
      # in case it isn't.
      timeout = request.form.get("timeout", default=60, type=int)

      required_files = request.form.getlist("required_files")

      # Extract the release code, if provided.
      if 'release' in request.files:
        release = request.files['release']
        save_or_extract(release, tempdir)

      # Extract all submitted submission files. While we extract, if any files
      # extracted are in the required_files list, we'll remove them as we go.
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

      # If required_files was provided and there are any elements remaining
      # after extracting the submission, the student didn't submit it. Return
      # an error.
      if required_files:
        return json.dumps({
          'error': 'NO COMPILE',
          'message': "Missing required files:\n\n" + "\n".join(required_files)
        })

      # Grab the test file, and append the OCaml code that will use Yojson to
      # get a JSON representation of the test results.
      t = request.files['test_file']
      test_filename = secure_filename(t.filename)
      test_file = open(os.path.join(tempdir, test_filename), "wb")
      t.save(test_file)
      test_file.writelines(paounit_json_response)
      test_file.close()

      # Compile the test file. The test file should use the student modules, and
      # thus those will get compiled in too. If the return code isn't 0, the
      # submission didn't compile and we can return an error.
      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson,str " + test_filename), stdout=subprocess.PIPE)
      if compiler.returncode != 0:
        return json.dumps({'error': 'NO COMPILE', "message": compiler.stdout.decode("utf-8")})
      # Now that the code is compiled, remove the test file source as it's not
      # needed. This should prevent student code from easily reading it.
      os.remove(os.path.join(tempdir, test_filename))
      os.remove(os.path.join(tempdir, "_build", test_filename))
      try:
        # Run the student code. We don't care about any output, so pipe that to
        # DEVNULL. Wait for timeout seconds.
        tester = subprocess.Popen(shlex.split("cs3110 test " + test_filename), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tester.wait(timeout=timeout)
      except subprocess.TimeoutExpired:
        # If the timeout occurred, we need to kill the test. Recurse through
        # any child processes and kill those too, just to be sure - otherwise,
        # the test process can potentially outlive this request and keep
        # consuming resources.
        parent = psutil.Process(tester.pid)
        children = parent.children(recursive=True)
        for child in children:
          child.kill()
        parent.kill()
        return json.dumps({'error': 'TIMEOUT EXPIRED', "message": "The timeout has expired."})
      # If we sucessfully ran the tests, results will be saved in
      # test-results.json. Send that back as the resposne.
      with open("test-results.json", "r") as results:
        return json.dumps({'results': json.load(results)})


@contextmanager
def cd(newdir):
  """Helper to allow changing directories as a context manager - the directory
  is changed when the manager is entered, and changed back when the manager is
  exited.
  """
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def get_file_extension(filename):
  """Helper to get the extension of a file. Returns None if the file has no
  extension.
  """
  try:
    return filename.rsplit('.', 1)[1]
  except IndexError:
    return None

def save_or_extract(file, target):
  """If the file is a .zip archive, it is extracted to the target path.
  Otherwise, it is simply saved there as-is."""
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
