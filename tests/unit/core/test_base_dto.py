import unittest
from uno.core.base import dto

class TestBaseDTO(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(dto)
