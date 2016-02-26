#!/usr/bin/env python3

from flask import Flask, render_template, request
import json
import shlex
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/test", methods=["POST"])
def test():
  f = request.files['test-file']
  f.save("ps1.ml")
  compiler = subprocess.run(shlex.split("cs3110 compile -p yojson ps1_test_public.ml"), stdout = subprocess.PIPE)
  if compiler.returncode != 0:
    return json.dumps([{'name': 'NO COMPILE', 'failed': True, "message": compiler.stdout.decode("utf-8")}])
  tester = subprocess.run(shlex.split("cs3110 test ps1_test_public.ml"), stdout = subprocess.PIPE, stderr = subprocess.DEVNULL)
  return tester.stdout

if __name__ == "__main__":
  app.debug = True
  use_debugger = True
  app.run(host="::")
