import unittest
from uno.core import feature_factory

class TestFeatureFactory(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(feature_factory)
