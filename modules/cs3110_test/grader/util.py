from contextlib import contextmanager
from werkzeug import secure_filename
import os
import zipfile

@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def get_file_extension(filename):
  return filename.rsplit('.', 1)[1]

def save_or_extract(file, target):
  if get_file_extension(file.filename) == "zip":
    release_archive = zipfile.ZipFile(file)
    release_archive.extractall(target)
  else:
    file.save(os.path.join(target, secure_filename(file.filename)))
