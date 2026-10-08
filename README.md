# MiniPy — Phase 1 + Phase 2 foundation

MiniPy is being built as a real installed desktop development environment, not a browser-only playground.

## Phase 1 — local execution

The execution core provides deterministic process execution for real local toolchains: Python, JavaScript, TypeScript, C, C++, and Java. HTML and CSS are native web capabilities. Execution returns stdout, stderr, exit code, and timeout state. Standard input is supported. Compiler diagnostics are preserved. No remote execution service is required.

## Phase 2 — runtime management

The runtime manager establishes the offline-first provisioning layer: explicit registry for the eight core languages; local runtime discovery; bundled-vs-system provenance; persistent runtime manifest; per-user runtime, bundle, and cache directories; SHA-256 verification; safe ZIP/TAR extraction; explicit provisioning only; and no implicit network downloads.

System discovery is separate from bundled provisioning. A release installer must ship verified runtime bundles so installed MiniPy does not depend on a user's pre-existing toolchain.

## Verification

    python -m unittest discover -s tests -v
    python -m minipy_core runtimes
    python -m minipy_core check-runtimes --save

Tests cover successful execution, stdin, compilation failures, timeouts, runtime discovery, manifest creation, checksum rejection, and archive extraction.

## Product requirement

After installation, MiniPy's core development workflow must work with networking disabled. Internet access is optional for updates, additional runtimes, uncached packages, Git, extensions, and online services.

No feature is considered certified merely because its runtime appears in the registry.
