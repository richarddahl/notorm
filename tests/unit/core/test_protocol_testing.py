import unittest
from uno.core import protocol_testing

class TestProtocolTesting(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(protocol_testing)
