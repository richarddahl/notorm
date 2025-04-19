import unittest
from uno.core import resources

class TestResources(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(resources)
