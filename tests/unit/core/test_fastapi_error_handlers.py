import unittest
from uno.core import fastapi_error_handlers

class TestFastAPIErrorHandlers(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(fastapi_error_handlers)
