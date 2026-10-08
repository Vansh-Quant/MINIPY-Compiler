import sys
import tempfile
import unittest
from pathlib import Path

from minipy_core import LocalExecutor, Runtime


class LocalExecutorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executor = LocalExecutor({
            "python": Runtime("python", Path(sys.executable)),
        }, timeout_seconds=0.5)

    def source(self, code):
        path = self.root / "main.py"
        path.write_text(code, encoding="utf-8")
        return path

    def test_real_python_execution(self):
        result = self.executor.run("python", self.source("print(sum(range(5)))"))
        self.assertEqual((result.stdout, result.stderr, result.exit_code, result.timed_out), ("10\n", "", 0, False))

    def test_interactive_input_is_supplied(self):
        result = self.executor.run("python", self.source("print(input().upper())"), "hello\n")
        self.assertEqual(result.stdout, "HELLO\n")

    def test_runtime_error_is_not_hidden(self):
        result = self.executor.run("python", self.source("raise ValueError('broken')"))
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("ValueError: broken", result.stderr)

    def test_timeout(self):
        result = self.executor.run("python", self.source("while True: pass"))
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.exit_code)

    def test_unknown_language_rejected(self):
        with self.assertRaises(ValueError):
            self.executor.run("java", self.source("print(1)"))

    def test_invalid_timeout_rejected(self):
        with self.assertRaises(ValueError):
            LocalExecutor({}, timeout_seconds=0)


if __name__ == "__main__":
    unittest.main()
