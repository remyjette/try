from contextlib import contextmanager

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
  if get_file_extension(f.filename) == "zip":
    release_archive = zipfile.ZipFile(f)
    release_archive.extractall(target)
  else:
    f.save(os.path.join(target, secure_filename(f.filename)))
