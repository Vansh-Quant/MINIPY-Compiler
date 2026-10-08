# MiniPy — Architecture Decision Record 001

**Status:** Accepted product direction; implementation in progress.

## Product contract

MiniPy is a Windows-first, installed, offline-first desktop IDE. The installer must provision local, real toolchains for Python, C, C++, Java, JavaScript, TypeScript, HTML, and CSS. A language is **not supported** until its offline compile/run/debug feature matrix passes. HTML/CSS are web document languages, not executable compiler targets.

The UI will be a premium, professional, VS Code-inspired workspace with optional student guidance. Projects progress from single-file to multi-file without changing storage formats. The native project directory is the source of truth.

## System boundaries

1. **Desktop shell:** installer, native filesystem and process access, OS integration.
2. **Workspace:** projects, files, settings, and project manifests.
3. **Execution:** language-specific build/run adapters and structured sessions.
4. **Toolchains:** locally installed/bundled real compilers, interpreters, debuggers, LSP servers.
5. **Services:** dependency manager, test runner, diagnostics, Git, terminal.
6. **Presentation:** editor, explorer, panels, learning explanations.

No handwritten interpreter may substitute for a language's real implementation. Remote execution is optional and never a prerequisite for core offline development.

## Current slice

The first Python module provides a deliberately small local-process execution boundary with structured stdout, stderr, exit code, stdin and timeout. It does **not** yet offer streaming interactive stdin, cancellation, process-tree termination, C/C++/Java build orchestration, a bundled toolchain, desktop packaging, or secure isolation. Those features are required before release. The executor currently requires a configured local executable and must only be used with trusted code.

## Engineering rules

- Small modules with one responsibility; avoid speculative layers.
- Tests before claiming a feature is supported.
- Never shell-interpolate source paths or arguments.
- No hidden network dependency for offline operations.
- Apply Ponytail after behavior is covered by tests: preserve behavior, remove redundancy, keep diffs focused.
- Preserve the existing prototype until the replacement is proven.

## Next engineering milestones

1. Runtime discovery and explicit bundle manifest, integrity verification.
2. Windows process-group lifecycle and sandbox policy.
3. Real compile/link/run adapters for C/C++, Java, JS/TS and web preview.
4. Desktop shell and signed installer with bundled runtimes.
5. Editor, terminal, LSP, debugging and package integrations.
6. Offline installer certification on clean Windows VMs.
