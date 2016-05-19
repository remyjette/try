import unittest
import studentcode

class TestStringMethods(unittest.TestCase):

    def test_fact(self):
        self.assertEqual(studentcode.fact(5), 120)

    def test_concat(self):
        self.assertEqual(studentcode.concat("hello ", "world"), "hello world")

