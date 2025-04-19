import unittest
from uno.core import types

class TestTypes(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(types)
