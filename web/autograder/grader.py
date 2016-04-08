from autograder.util import cd
from distutils.dir_util import copy_tree
from werkzeug import secure_filename
import json
import os
import shlex
import shutil
import subprocess
import tempfile

def grade(submission_dir, testfile, release_dir=None):

  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):

      if (release_dir):
        copy_tree(release_dir, tempdir)

      copy_tree(submission_dir, tempdir)

      shutil.copy(
        testfile.path,
        os.path.join(tempdir, testfile.filename)
      )

      #THIS SHOULD HAND OFF TO LANGUAGE MODULE
      #OCAML MODULE BELOW
      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + testfile.filename), stdout = subprocess.PIPE)
      if compiler.returncode != 0:
        return [{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}]
      tester = subprocess.run(shlex.split("cs3110 test " + testfile.filename), stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
      return json.loads(tester.stdout.decode("utf-8"))

