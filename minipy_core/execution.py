from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class ExecutionResult:
    command: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


class ExecutionError(RuntimeError):
    pass


class LocalExecutor:
    """Deterministic process runner shared by language adapters."""

    def run(self, command: Sequence[str], *, cwd: Path | None = None,
            stdin: str = "", timeout: float = 10) -> ExecutionResult:
        try:
            process = subprocess.run(
                list(command), input=stdin, capture_output=True, text=True,
                cwd=cwd, timeout=timeout, check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(tuple(command), exc.stdout or "", exc.stderr or "", None, True)
        except OSError as exc:
            raise ExecutionError(str(exc)) from exc
        return ExecutionResult(tuple(command), process.stdout, process.stderr, process.returncode, False)


class LanguageRunner:
    def __init__(self, executor: LocalExecutor | None = None):
        self.executor = executor or LocalExecutor()

    def python(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        return self._script("python", source, ".py", stdin=stdin, timeout=timeout)

    def javascript(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        return self._script("node", source, ".js", stdin=stdin, timeout=timeout)

    def typescript(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        import shutil
        tsc, node = shutil.which("tsc"), shutil.which("node")
        if not tsc or not node:
            raise ExecutionError("TypeScript requires tsc and node")
        with self._source(source, ".ts") as path:
            compile_result = self.executor.run(
                (tsc, str(path), "--target", "ES2022", "--module", "CommonJS",
                 "--outDir", str(path.parent)),
                timeout=timeout,
            )
            if compile_result.exit_code != 0 or compile_result.timed_out:
                return compile_result
            return self.executor.run((node, str(path.with_suffix(".js"))),
                                     stdin=stdin, timeout=timeout)

    def _script(self, runtime: str, source: str, suffix: str, *, stdin: str,
                timeout: float) -> ExecutionResult:
        import shutil
        executable = shutil.which(runtime)
        if not executable:
            raise ExecutionError(f"Runtime not found: {runtime}")
        with self._source(source, suffix) as path:
            return self.executor.run((executable, str(path)), stdin=stdin, timeout=timeout)

    def c(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        return self._compile_and_run("gcc", source, ".c", stdin=stdin, timeout=timeout)

    def cpp(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        return self._compile_and_run("g++", source, ".cpp", stdin=stdin, timeout=timeout)

    def java(self, source: str, *, stdin: str = "", timeout: float = 10) -> ExecutionResult:
        import shutil
        javac, java = shutil.which("javac"), shutil.which("java")
        if not javac or not java:
            raise ExecutionError("Java requires javac and java")
        with self._source(source, ".java") as path:
            result = self.executor.run((javac, str(path)), timeout=timeout)
            if result.exit_code != 0 or result.timed_out:
                return result
            return self.executor.run(
                (java, "-cp", str(path.parent), path.stem),
                stdin=stdin, timeout=timeout,
            )

    def _compile_and_run(self, compiler: str, source: str, suffix: str,
                         *, stdin: str, timeout: float) -> ExecutionResult:
        import shutil
        compiler_path = shutil.which(compiler)
        if not compiler_path:
            raise ExecutionError(f"Compiler not found: {compiler}")
        with self._source(source, suffix) as path:
            binary = path.with_suffix("")
            compile_result = self.executor.run(
                (compiler_path, str(path), "-o", str(binary)), timeout=timeout
            )
            if compile_result.exit_code != 0 or compile_result.timed_out:
                return compile_result
            return self.executor.run((str(binary),), stdin=stdin, timeout=timeout)

    @staticmethod
    def _source(source: str, suffix: str):
        import shutil
        import tempfile

        class Source:
            def __enter__(self):
                self.directory = Path(tempfile.mkdtemp())
                stem = "Main" if suffix == ".java" else "main"
                self.path = self.directory / f"{stem}{suffix}"
                self.path.write_text(source, encoding="utf-8")
                return self.path

            def __exit__(self, exc_type, exc, tb):
                shutil.rmtree(self.directory, ignore_errors=True)

        return Source()
