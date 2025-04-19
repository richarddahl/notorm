import unittest
from uno.core.base import error

class TestBaseError(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(error)
