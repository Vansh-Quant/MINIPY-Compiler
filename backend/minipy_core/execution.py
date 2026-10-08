"""Run real local language toolchains without shell interpolation.

This module is a development foundation, not a security sandbox. Never execute
untrusted code without operating-system isolation and resource limits.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Mapping


@dataclass(frozen=True)
class Runtime:
    language: str
    executable: Path
    arguments: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


class LocalExecutor:
    def __init__(self, runtimes: Mapping[str, Runtime], timeout_seconds: float = 10):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.runtimes = dict(runtimes)
        self.timeout_seconds = timeout_seconds

    def run(self, language: str, source: Path, stdin: str = "") -> ExecutionResult:
        runtime = self.runtimes.get(language)
        if runtime is None:
            raise ValueError(f"Unsupported or unconfigured runtime: {language}")
        source = source.resolve(strict=True)
        if not source.is_file():
            raise ValueError("Source must be a file")
        executable = runtime.executable.resolve(strict=True)
        if not executable.is_file():
            raise ValueError("Runtime executable must be a file")
        command = [str(executable), *runtime.arguments, str(source)]
        try:
            completed = subprocess.run(
                command,
                input=stdin,
                text=True,
                capture_output=True,
                cwd=source.parent,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return ExecutionResult(
                stdout=_decode(error.stdout),
                stderr=_decode(error.stderr),
                exit_code=None,
                timed_out=True,
            )
        return ExecutionResult(completed.stdout, completed.stderr, completed.returncode, False)


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
