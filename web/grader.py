from distutils.dir_util import copy_tree

def grade(submission, testfile, release_dir=None):

  with tempfile.TemporaryDirectory() as tempdir:
    with cd(tempdir):

      if (release_dir):
        copy_tree(release_dir, tempdir)

      filename = secure_filename(submission.filename)
      submission.save(os.path.join(tempdir, filename))

      shutil.copy(
        os.path.join(app.config["TESTFILE_DIR"], testfile.filename),
        os.path.join(tempdir, testfile.filename)
      )

      #THIS SHOULD HAND OFF TO LANGUAGE MODULE
      #OCAML MODULE BELOW
      compiler = subprocess.run(shlex.split("cs3110 compile -p yojson " + assignment.testfile), stdout = subprocess.PIPE)
      if compiler.returncode != 0:
        return [{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}]
      tester = subprocess.run(shlex.split("cs3110 test " + assignment.testfile), stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
      return json.loads(tester.stdout)

