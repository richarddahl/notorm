import unittest
from uno.core import caching

class TestCaching(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(caching)
