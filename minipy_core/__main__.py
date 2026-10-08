from __future__ import annotations

import argparse
import json
from pathlib import Path

from .execution import LanguageRunner
from .runtime import RuntimeManager


def main() -> int:
    parser = argparse.ArgumentParser(prog="minipy")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("runtimes")
    check = sub.add_parser("check-runtimes")
    check.add_argument("--save", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("language", choices=["python", "javascript", "typescript", "c", "cpp", "java"])
    run.add_argument("file", type=Path)
    run.add_argument("--stdin", default="")
    args = parser.parse_args()

    manager = RuntimeManager()
    if args.command == "runtimes":
        print(json.dumps({k: vars(v) for k, v in manager.discover().items()}, indent=2))
        return 0
    if args.command == "check-runtimes":
        statuses = manager.discover()
        if args.save:
            manager.save_manifest(statuses)
        missing = manager.verify_core(statuses)
        print("all core runtimes available" if not missing else "missing: " + ", ".join(missing))
        return 0 if not missing else 1

    source = args.file.read_text(encoding="utf-8")
    result = getattr(LanguageRunner(), args.language)(source, stdin=args.stdin)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return 124 if result.timed_out else (result.exit_code or 0)


if __name__ == "__main__":
    raise SystemExit(main())
