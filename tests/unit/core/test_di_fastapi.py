import unittest
from uno.core import di_fastapi

class TestDIFastAPI(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(di_fastapi)
