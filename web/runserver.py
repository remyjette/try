#!/usr/bin/env python3

from autograder import app

if __name__ == "__main__":
  app.debug = True
  use_debugger = True
  app.run(host="127.0.0.1", port=8000)
