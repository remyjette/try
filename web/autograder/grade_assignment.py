import csv
import itertools
import os
import tempfile
import zipfile
from autograder.models import Unittest, Testfile
from flask_sqlalchemy import get_debug_queries

def grade_assignment(assignment, submissions):
  """Grade all of the submissions in the given archive.

  This function expects a path to a zip archive that contains a single directory
  "Submissions" that contains a subdirectory for each student's submission. It
  will grade each of these submissions against the test cases in the given
  assignment, then calculate grades and produce a CSV of the results.

  Note: This function is somewhat specific to Cornell CMS. The structure of
  the generated CSV result file is made to conform to CMS's expected input.
  This function will need to be substantially if a different spec is required
  for the generated CSV, but fortunately this is the only part of this
  autograder that is coded to a specific external dependency.
  """
  csvfile = tempfile.NamedTemporaryFile(mode="w+", newline="")
  with tempfile.TemporaryDirectory() as tempdir:
    fieldnames = (['NetID']
        + ([p.problem_name for p in assignment.problems] if assignment.problems else ["Grade"])
        + (["Adjustment","Total"] if assignment.problems else [])
        + ['Add Comments'])
    gradeswriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
    gradeswriter.writeheader()

    final_results = []

    submissions_archive = zipfile.ZipFile(submissions)
    submissions_archive.extractall(tempdir)
    submissions_directory = os.path.join(tempdir, "Submissions")

    for submission in os.listdir(submissions_directory):
      filenames = os.listdir(os.path.join(submissions_directory, submission))
      files = [os.path.join(submissions_directory, submission, filename) for filename in filenames]
      # Each submission is sent to a grader server via testfile.grade to have
      # unit tests actually compiled and run.
      grader_response = {
          testfile.filename: testfile.grade(files, public_only=False)
          for testfile in assignment.testfiles
      }

      # Once we have a response from the grader, inspect the results to
      # compute a score and write comments for the student.
      test_results = {"NetID": submission}
      comments = "## Automated test results for '" + submission + "' ##"

      if assignment.problems:
        grades = {p.problem_name: 0 for p in assignment.problems}
      else:
        grades = {"Grade": 0}

      error_types = set()

      for testfile in assignment.testfiles:
        results = grader_response[testfile.filename]
        comments += "\n### " + testfile.filename + " ###\n\n"

        if "error" in results:
          # If the student's test response is an error, let them know and
          # then move on - they'll get a zero for all tests.
          comments += "Error: " + results["error"] + "\n" + results["message"] + "\n\n"
          error_types.add(results["error"])
          continue

        for unittest in testfile.unittests:
          if unittest.weight == 0:
            # If this test isn't worth anything, skip it.
            continue
          test_case = [r for r in results["results"] if r["name"] == unittest.friendly_name]

          if test_case:
            test_case = test_case[0]
            passed = test_case["passed"]
            message = test_case["message"].partition("\n")[0] if test_case["message"] is not None else None
            score = unittest.weight if passed else 0
          else:
            raise Exception("Could not find a result for test '" + unittest.friendly_name + "'")

          if assignment.problems:
            # TODO validate unittest problems - make sure that they all map to an assignment problem
            grades[unittest.problem] += score
          else:
            grades["Grade"] += score

          comments += (("PASS" if passed else "FAIL") + " -- "
            + unittest.friendly_name
            + (" -- " + message if message is not None else "") + "\n")

      if assignment.problems:
        for problem in assignment.problems:
          weight_total = sum(u.weight for t in assignment.testfiles for u in t.unittests if u.problem == problem.problem_name)
          if weight_total == 0:
            # no tests for this problem
            # TODO maybe show a warning?
            continue
          grades[problem.problem_name] = round(grades[problem.problem_name] / weight_total * problem.score)
      else:
        weight_total = sum(u.weight for t in assignment.testfiles for u in t.unittests)
        # TODO what if no tests defined or weight total is 0 for all tests?
        # TOOD ensure non-negative tests
        grades["Grade"] = round(grades["Grade"] / weight_total * assignment.max_score)
      test_results.update(grades)
      test_results["Add Comments"] = comments

      # In Cornell CMS, group submissions look like 'group_of_user1_user2'.
      # However, the score CSV must contain a separate row for each student, and
      # must NOT contain any group_of_ rows as the grades table stores by
      # student rather than group. Thus, for group submissions we clone the row
      # for each student in the group, changing the NetID each time.
      if submission.startswith("group_of_"):
        netids = submission.replace("group_of_", "").split("_")
        for netid in netids:
          r = test_results.copy()
          r["NetID"] = netid
          gradeswriter.writerow(r)
      else:
        gradeswriter.writerow(test_results)

      # add the test results to the 'final_results' dict for calculating stats
      # in JavaScript on the results page. The comments aren't needed for the
      # statistics though, so we remove them to substantially decrease the
      # amount of data sent.
      del test_results["Add Comments"]
      test_results["_error_types"] = list(error_types)
      final_results.append(test_results)

    csvfile.seek(0)
    return (csvfile, final_results)
