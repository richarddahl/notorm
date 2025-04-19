import unittest
from uno.core.asynchronous import task_manager


class TestTaskManager(unittest.TestCase):
    def test_module_import(self):
        self.assertIsNotNone(task_manager)
