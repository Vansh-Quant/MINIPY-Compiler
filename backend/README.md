# MiniPy local execution foundation

This module executes configured **real local executables**, not simulated languages. It is a development-only building block and **not a sandbox**.

Run the unit tests from the repository root:

```bash
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = 'backend'
python -m unittest discover -s backend/tests -v
```

A local Python interpreter is needed to run the development tests. End users will not be expected to install toolchains separately once MiniPy's offline installer is implemented.
