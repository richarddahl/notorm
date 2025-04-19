import unittest
from uno.core.async import concurrency

class TestConcurrency(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(concurrency)
