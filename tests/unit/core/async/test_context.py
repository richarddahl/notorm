import unittest
from uno.core.async import context

class TestContext(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(context)
