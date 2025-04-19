import unittest
from uno.core import protocols

class TestProtocolsModule(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(protocols)
