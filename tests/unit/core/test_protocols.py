import unittest
from uno.core import protocols

class TestProtocols(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(protocols)
