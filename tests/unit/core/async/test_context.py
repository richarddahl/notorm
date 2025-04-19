import unittest
from uno.core.asynchronous import context


class TestContext(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(context)
