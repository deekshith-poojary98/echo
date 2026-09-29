# Installation

Install a CLI that runs `.echo` files. Needs **Python 3.10+**.

Prefer the command name **`elang`**. Many shells already treat `echo` as a built-in (POSIX `echo`; `Write-Output` on PowerShell). The package also registers `echolang` and `echo`; docs and examples use `elang`.

The PyPI package name is **`echolang`**.

`examples/` ships with the git repository only — it is **not** installed by pip/pipx. After a PyPI install, verify with `--version` and a small file you create yourself.

## Option 1: pipx (recommended)

Isolated env, global commands.

### macOS / Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install echolang
```

### Windows PowerShell

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install echolang
```

### Open a new terminal

`pipx ensurepath` updates your shell config files. It does **not** refresh the PATH in the terminal where you just ran it. **Open a new terminal window** (or start a new shell session) before continuing.

### Verify the install

```bash
elang --version
```

The command prints `Echo` followed by the installed version and exits 0. The version string is whatever you installed from PyPI (or from a clone). This repository’s package version is **2.1.9**.

Optional sanity checks that do not need a checkout:

```bash
elang builtins --count
elang std
```

### If `elang: command not found`

1. Confirm you opened a **new** terminal after `ensurepath`.
2. Re-run path setup explicitly:

   ```bash
   python3 -m pipx ensurepath
   ```

   On Windows PowerShell: `python -m pipx ensurepath`, then open a new session.

3. On macOS / Linux, check that `~/.local/bin` is on your PATH (pipx usually installs shims there):

   ```bash
   ls ~/.local/bin/elang
   echo "$PATH"
   ```

   If the binary exists but PATH is wrong, add `~/.local/bin` to PATH in your shell profile, then open a new terminal.

4. Confirm the package is installed: `pipx list` should show `echolang`.

### First program

Create `hello.echo` in any directory:

```echo
say("Hello, Echo!");
```

Run it:

```bash
elang hello.echo
```

Output:

```text
Hello, Echo!
```

Next: [Quick Start](/getting-started/quick-start).

### From GitHub (still no clone required)

```bash
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

Same verify → hello.echo journey as above.

## Option 2: From a clone (repo root)

Clone the repository, then install from the repo root. The `examples/` tree is available only in this layout.

```bash
git clone https://github.com/deekshith-poojary98/echo.git
cd echo
pip install .
# or for development: pip install -e .
```

From the **repo root**, you can run shipped examples:

```bash
elang examples/language_feature_smoke.echo
```

Editable install (development):

```bash
pip install -e .
```

## Commands

- `elang path/to/file.echo` — run
- `elang check [paths...]`
- `elang test [paths...]`
- `elang fmt [paths...] [--check]`
- `elang lint [paths...]`
- `elang builtins` / `elang builtins --count`
- `elang std` / `elang std --exports`
- `elang lsp`

No path on `elang` / `echolang` / `echo` alone starts the REPL (see [CLI and Execution Model](/reference/cli-and-execution-model)).

## See Also

- [Quick Start](/getting-started/quick-start)
- [CLI and Execution Model](/reference/cli-and-execution-model)
