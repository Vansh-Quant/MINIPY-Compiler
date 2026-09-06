# MiniPy

MiniPy is a modern, multi-language programming environment designed to make real software development accessible from a single workspace.

Instead of recreating simplified versions of programming languages, MiniPy integrates real language runtimes, compilers, toolchains, package ecosystems, and WebAssembly technologies wherever possible.

Users can create projects, write multi-file programs, install libraries, compile and execute code, provide input, inspect output and compiler diagnostics, debug programs, run tests, and build web applications — all from one unified interface.

MiniPy is designed around a modular execution architecture that supports languages such as Python, JavaScript, TypeScript, C, C++, Java, HTML, and CSS, while providing a foundation for adding additional languages and toolchains in the future.

The current repository contains the real-engine rebuild snapshot. Backend work is continuing toward a complete execution platform; features are only considered supported when they are implemented and tested against the underlying runtime/toolchain.

## Current real-engine architecture

- **Python:** CPython through Pyodide/WebAssembly in the browser.
- **JavaScript:** the browser's real JavaScript engine in an isolated worker execution path.
- **TypeScript:** the real TypeScript compiler bundle, transpiled to JavaScript and executed by the real JavaScript engine. Full type-checking is still a backend work item.
- **C / C++ / Java:** real GCC/G++/OpenJDK toolchains through Judge0 CE remote execution.
- **HTML / CSS:** browser-native web execution and styling.

## Repository status

This is an active engineering repository. The frontend is intentionally kept secondary while the execution backend, language coverage, package support, I/O, diagnostics, and testing infrastructure are being hardened.

Do not interpret a language entry in the UI as a claim that every language feature or every library is already certified. The goal is to certify real functionality through automated and cross-runtime tests before expanding the supported surface.

## Local files

- `MiniPy.html` — current application build.
- `tests/test_pyodide.js` — direct Pyodide/CPython smoke test.
- `tests/test_stdin.js` — Pyodide stdin smoke test.

## Development direction

The planned execution architecture is modular:

```text
MiniPy
  ├── Project System
  ├── Editor
  ├── Execution Engine
  │    ├── Python / Pyodide
  │    ├── JavaScript
  │    ├── TypeScript
  │    ├── C / C++ toolchain
  │    ├── Java toolchain
  │    └── Web runtime
  ├── Package System
  ├── Build System
  ├── Diagnostics
  ├── Test System
  ├── Terminal / I/O
  ├── Storage
  └── Security / Resource Controls
```

The project will be expanded incrementally, with real runtimes and toolchains preferred over handwritten language implementations.
