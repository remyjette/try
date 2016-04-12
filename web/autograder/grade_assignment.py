import csv
import itertools
import os
import tempfile
import zipfile
from autograder.models import Unittest, Testfile
from flask_sqlalchemy import get_debug_queries

def grade_assignment(assignment, submissions):
  csvfile = tempfile.NamedTemporaryFile(mode="w+", newline="")
  with tempfile.TemporaryDirectory() as tempdir:
    unittests = Unittest.query.filter(Testfile.assignment == assignment).all()

    fieldnames = ['NetID'] + [u.friendly_name for u in unittests] + ['Add Comments']
    gradeswriter = csv.DictWriter(csvfile, fieldnames=fieldnames, restval="0")
    gradeswriter.writeheader()

    submissions_archive = zipfile.ZipFile(submissions)
    submissions_archive.extractall(tempdir)
    submissions_directory = os.path.join(tempdir, "Submissions")

    for submission in os.listdir(submissions_directory):
      filenames = os.listdir(os.path.join(submissions_directory, submission))
      files = [os.path.join(submissions_directory, submission, filename) for filename in filenames]
      results = list(itertools.chain.from_iterable(
        testfile.grade(files, public_only=False) for testfile in assignment.testfiles
      ))

      test_results = {"NetID": submission}
      comments = ""

      for unittest in unittests:
        test_case = next((r for r in results if r["name"] == unittest.friendly_name))
        #TODO: WEIGHTS
        if test_case:
          passed = test_case["passed"]
          message = test_case["message"].partition("\n")[0] if test_case["message"] is not None else None
        else:
          passed = False
          message = "NO COMPILE"

        test_results[unittest.friendly_name] = 1 if passed else 0
        comments += (("PASS" if passed else "FAIL") + " -- "
          + unittest.friendly_name
          + (" -- " + message if message is not None else "") + "\n")

      test_results["Add Comments"] = comments
      gradeswriter.writerow(test_results)

    csvfile.seek(0)
    return csvfile
