import unittest
from uno.core import fastapi_integration

class TestFastAPIIntegration(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(fastapi_integration)
