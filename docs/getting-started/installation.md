# Installation

Install a CLI that runs `.echo` files. Needs **Python 3.10+**.

Prefer the command name **`elang`**. Many shells already treat `echo` as a built-in (`Write-Output` on PowerShell; POSIX `echo`). The package also registers `echolang` and `echo`; docs and examples use `elang`.

The PyPI package name is **`echolang`**. The first public upload is planned for **0.8.9**; until then, install from GitHub or a clone.

## Option 1: pipx (recommended)

Isolated env, global commands.

### Windows PowerShell

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

```powershell
elang examples\language_feature_smoke.echo
```

### macOS / Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

```bash
elang examples/language_feature_smoke.echo
```

### After PyPI (0.8.9+)

```bash
pipx install echolang
```

That installs the package `echolang` and puts **`elang`** (and `echolang`) on your PATH.

## Option 2: pip from a clone

```bash
pip install .
elang path/to/file.echo
```

## Option 3: editable install (development)

```bash
pip install -e .
```

## Commands

- `elang path/to/file.echo` — run
- `elang check [paths...]`
- `elang test [paths...]`
- `elang fmt [paths...] [--check]`
- `elang lint [paths...]`

No path on `elang` / `echolang` / `echo` alone starts the REPL (see [CLI and Execution Model](/reference/cli-and-execution-model)).

## Without installing

From the repo:

```bash
python src/main.py examples/language_feature_smoke.echo
python src/main.py examples/language_feature_smoke.echo --plain
# or: ./elang examples/language_feature_smoke.echo
```

## See Also

- [Quick Start](/getting-started/quick-start)
- [CLI and Execution Model](/reference/cli-and-execution-model)
