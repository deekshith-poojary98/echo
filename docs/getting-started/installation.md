# Installation

## Overview
Echo can be installed as a real CLI runtime so you can execute `.echo` files with a language command.

## Prerequisites
- Python 3.10+

## Option 1: Install with pipx (recommended)
`pipx` installs Echo in an isolated environment and exposes commands globally.

### Windows PowerShell
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

Run Echo:
```powershell
echolang examples\language_feature_smoke.echo
```

### macOS / Linux
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

Run Echo:
```bash
echolang examples/language_feature_smoke.echo
```

## Option 2: Install from source with pip
If you have cloned the repository:

```bash
pip install .
```

Run Echo:
```bash
echolang path/to/file.echo
```

## Option 3: Editable install for development
```bash
pip install -e .
```

## Available Commands
- `echolang path/to/file.echo`

The package also exposes an `echo` command, but most shells already reserve `echo` as a built-in command, so `echolang` is the reliable command to document and use.

In PowerShell, `echo` maps to `Write-Output`. In POSIX shells, `echo` is also typically a shell built-in.

## Example
```bash
echolang examples/language_feature_smoke.echo
```

## Notes
- Echo still supports direct execution with Python if needed:

```bash
python src/main.py examples/language_feature_smoke.echo
python src/main.py examples/language_feature_smoke.echo --plain
```

## See Also
- [Quick Start](/getting-started/quick-start)
- [CLI and Execution Model](/reference/cli-and-execution-model)
