#!/usr/bin/env python3

import os
import shutil
from autograder import db
from autograder.models import Course

def main():
  """Delete any uploaded release/test files and wipe the database.

  The paths are hardcoded, assuming that the release and test files directories
  are in the same folder, and that the program is using a SQLite DB file named
  "autograder.db" to store data.
  The values are hardcoded because this is only meant to be used on a dev
  version of the server. If you need to delete things in production, use the
  web interface.
  """
  shutil.rmtree("release_code", ignore_errors=True)
  shutil.rmtree("test_files", ignore_errors=True)
  os.unlink("autograder.db")
  db.create_all()

if __name__ == "__main__":
  main()
