import tempfile
import unittest
import zipfile
from pathlib import Path

from minipy_core.execution import LanguageRunner
from minipy_core.runtime import RuntimeManager


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = LanguageRunner()

    def test_python(self):
        r = self.runner.python('name = input(); print(f"Hello {name}")', stdin="Vansh\n")
        self.assertEqual(r.exit_code, 0)
        self.assertEqual(r.stdout.strip(), "Hello Vansh")

    def test_javascript(self):
        r = self.runner.javascript("console.log(2 ** 10)")
        self.assertEqual(r.stdout.strip(), "1024")

    def test_typescript(self):
        r = self.runner.typescript("const value: number = 42; console.log(value)")
        self.assertEqual(r.exit_code, 0)
        self.assertEqual(r.stdout.strip(), "42")

    def test_c(self):
        r = self.runner.c('#include <stdio.h>\nint main(){ printf("C\\n"); }')
        self.assertEqual(r.stdout.strip(), "C")

    def test_cpp(self):
        r = self.runner.cpp('#include <iostream>\nint main(){ std::cout << "C++\\n"; }')
        self.assertEqual(r.stdout.strip(), "C++")

    def test_java(self):
        r = self.runner.java('public class Main { public static void main(String[] a){ System.out.println("Java"); } }')
        self.assertEqual(r.stdout.strip(), "Java")

    def test_compile_error(self):
        r = self.runner.c("int main( {")
        self.assertNotEqual(r.exit_code, 0)
        self.assertTrue(r.stderr)

    def test_timeout(self):
        r = self.runner.python("while True: pass", timeout=0.2)
        self.assertTrue(r.timed_out)
        self.assertIsNone(r.exit_code)


class RuntimeManagerTests(unittest.TestCase):
    def test_manifest_and_core_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            manager = RuntimeManager(Path(temp) / "minipy")
            statuses = manager.discover()
            self.assertTrue(statuses["html"].installed)
            self.assertTrue(statuses["css"].installed)
            manager.save_manifest(statuses)
            self.assertTrue(manager.manifest_path.exists())

    def test_zip_bundle_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "payload"
            source.mkdir()
            (source / "python.exe").write_text("runtime", encoding="utf-8")
            bundle = root / "python.zip"
            with zipfile.ZipFile(bundle, "w") as zf:
                zf.write(source / "python.exe", "bin/python.exe")
            manager = RuntimeManager(root / "minipy")
            destination = manager.install_bundle(bundle, "python")
            self.assertTrue((destination / "payload" / "bin" / "python.exe").exists())

    def test_bundle_checksum(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manager = RuntimeManager(root / "minipy")
            bundle = root / "runtime.bin"
            bundle.write_bytes(b"mini-runtime")
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                manager.install_bundle(bundle, "python", sha256="0" * 64)


if __name__ == "__main__":
    unittest.main()
