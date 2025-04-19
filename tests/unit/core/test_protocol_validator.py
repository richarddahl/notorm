import unittest
from uno.core import protocol_validator

class TestProtocolValidator(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(protocol_validator)
