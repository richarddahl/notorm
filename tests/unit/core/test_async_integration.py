import unittest
from uno.core import async_integration

class TestAsyncIntegration(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(async_integration)
