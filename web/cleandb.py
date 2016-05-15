#!/usr/bin/env python3

import os
import shutil
from autograder import db
from autograder.models import Course

def main():
  shutil.rmtree("release_code", ignore_errors=True)
  shutil.rmtree("test_files", ignore_errors=True)
  os.unlink("autograder.db")
  db.create_all()
  c = Course("cs3110", "")
  db.session.add(c)
  db.session.commit()

if __name__ == "__main__":
  main()
