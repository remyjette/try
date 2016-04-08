import itertools
import os
import tempfile
import zipfile

def grade_assignment(assignment, submissions):
  with tempfile.TemporaryDirectory() as tempdir:
    submissions_archive = zipfile.ZipFile(submissions)
    submissions_archive.extractall(tempdir)
    submissions_directory = os.path.join(tempdir, "Submissions")
    test_results = {}
    for submission in os.listdir(submissions_directory):
      filenames = os.listdir(os.path.join(submissions_directory, submission))
      files = [os.path.join(submissions_directory, submission, filename) for filename in filenames]
      results = list(itertools.chain.from_iterable(
        testfile.grade(files, public_only=False) for testfile in assignment.testfiles
      ))
      test_results[submission] = results
    return test_results
