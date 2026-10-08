from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CORE_RUNTIMES = ("python", "javascript", "typescript", "c", "cpp", "java", "html", "css")


@dataclass(frozen=True)
class RuntimeSpec:
    id: str
    name: str
    version: str
    executable: str
    aliases: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class RuntimeStatus:
    id: str
    installed: bool
    executable: str | None
    version: str | None
    source: str | None
    bundled: bool
    error: str | None = None


DEFAULT_SPECS = (
    RuntimeSpec("python", "Python", "3", "python", ("python3",)),
    RuntimeSpec("javascript", "JavaScript", "22", "node"),
    RuntimeSpec("typescript", "TypeScript", "5", "tsc"),
    RuntimeSpec("c", "C", "17", "gcc", ("clang",)),
    RuntimeSpec("cpp", "C++", "20", "g++", ("clang++",)),
    RuntimeSpec("java", "Java", "21", "javac"),
    RuntimeSpec("html", "HTML", "browser", ""),
    RuntimeSpec("css", "CSS", "browser", ""),
)


class RuntimeError(RuntimeError):
    pass


class RuntimeManager:
    """Discover and provision explicitly supplied local runtime bundles."""

    def __init__(self, root: Path | None = None, specs: Iterable[RuntimeSpec] = DEFAULT_SPECS):
        self.root = Path(root or os.environ.get("MINIPY_HOME", Path.home() / ".minipy"))
        self.runtimes_dir = self.root / "runtimes"
        self.bundles_dir = self.root / "bundles"
        self.cache_dir = self.root / "cache"
        self.specs = {spec.id: spec for spec in specs}
        for path in (self.runtimes_dir, self.bundles_dir, self.cache_dir):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def manifest_path(self) -> Path:
        return self.root / "runtime-manifest.json"

    def discover(self) -> dict[str, RuntimeStatus]:
        statuses = {}
        for spec in self.specs.values():
            if spec.id in {"html", "css"}:
                statuses[spec.id] = RuntimeStatus(spec.id, True, None, "browser", "builtin", True)
                continue
            executable = self._find_executable(spec)
            if not executable:
                statuses[spec.id] = RuntimeStatus(spec.id, False, None, None, None, False)
                continue
            try:
                version = self._version(executable, spec.id)
                bundled = self._is_bundled(executable)
                statuses[spec.id] = RuntimeStatus(
                    spec.id, True, str(executable), version,
                    "bundle" if bundled else "system", bundled,
                )
            except OSError as exc:
                statuses[spec.id] = RuntimeStatus(
                    spec.id, False, str(executable), None, None, False, str(exc)
                )
        return statuses

    def save_manifest(self, statuses: dict[str, RuntimeStatus] | None = None) -> Path:
        statuses = statuses or self.discover()
        payload = {
            "schema": 1,
            "platform": platform.platform(),
            "runtimes": [asdict(status) for status in statuses.values()],
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.manifest_path

    def verify_core(self, statuses: dict[str, RuntimeStatus] | None = None) -> list[str]:
        statuses = statuses or self.discover()
        return [rid for rid in CORE_RUNTIMES if not statuses[rid].installed]

    def install_bundle(self, bundle: Path, runtime_id: str,
                       sha256: str | None = None) -> Path:
        if runtime_id not in self.specs or runtime_id in {"html", "css"}:
            raise RuntimeError(f"Unsupported bundle target: {runtime_id}")
        bundle = Path(bundle)
        if not bundle.is_file():
            raise RuntimeError(f"Bundle not found: {bundle}")
        if sha256 and self._sha256(bundle) != sha256.lower():
            raise RuntimeError("Bundle checksum mismatch")

        destination = self.runtimes_dir / runtime_id
        staging = Path(tempfile.mkdtemp(prefix=f"{runtime_id}-", dir=self.runtimes_dir))
        try:
            if zipfile.is_zipfile(bundle):
                self._extract_zip(bundle, staging / "payload")
            elif tarfile.is_tarfile(bundle):
                self._extract_tar(bundle, staging / "payload")
            else:
                shutil.copy2(bundle, staging / bundle.name)
            if destination.exists():
                shutil.rmtree(destination)
            staging.rename(destination)
            return destination
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def bundle_metadata(self, runtime_id: str, version: str, archive: Path) -> dict[str, str]:
        archive = Path(archive)
        return {
            "id": runtime_id,
            "version": version,
            "platform": f"{platform.system().lower()}-{platform.machine().lower()}",
            "sha256": self._sha256(archive),
            "file": archive.name,
        }

    def _find_executable(self, spec: RuntimeSpec) -> Path | None:
        bundled = self.runtimes_dir / spec.id
        for candidate in (spec.executable, *spec.aliases):
            if not candidate:
                continue
            local = self._bundled_executable(bundled, candidate)
            if local:
                return local
            found = shutil.which(candidate)
            if found:
                return Path(found)
        return None

    @staticmethod
    def _bundled_executable(root: Path, name: str) -> Path | None:
        if not root.exists():
            return None
        names = [name, f"{name}.exe"] if os.name == "nt" and not name.endswith(".exe") else [name]
        for candidate in names:
            for path in root.rglob(candidate):
                if path.is_file():
                    return path
        return None

    def _is_bundled(self, executable: Path) -> bool:
        try:
            executable.resolve().relative_to(self.runtimes_dir.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def _version(executable: Path, runtime_id: str) -> str:
        command = [str(executable), "-version"] if runtime_id == "java" else [str(executable), "--version"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        output = (result.stdout + result.stderr).strip().splitlines()
        if result.returncode != 0 or not output:
            raise RuntimeError(f"Unable to read {runtime_id} version")
        return output[0]

    @staticmethod
    def _safe_member_path(root: Path, member: str) -> Path:
        target = (root / member).resolve()
        if target != root.resolve() and root.resolve() not in target.parents:
            raise RuntimeError("Unsafe runtime bundle path")
        return target

    def _extract_zip(self, archive: Path, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                target = self._safe_member_path(destination, info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink)

    def _extract_tar(self, archive: Path, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive) as tf:
            for member in tf.getmembers():
                self._safe_member_path(destination, member.name)
            tf.extractall(destination)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
