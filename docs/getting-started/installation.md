# Installation

This page helps you put Echo on your computer and run your first program.

You will:

1. Open a **Terminal** (a window where you type commands).
2. Install Echo.
3. Check that Echo works.
4. Create a file named `hello.echo`.
5. Run it and see `Hello, Echo!`

Want to try Echo **without** installing? Use the [Playground](/playground) first, then come back here.

---

## What is a Terminal?

A **Terminal** (sometimes called a command line) is an app where you type short commands and press Enter. Echo’s install steps use the Terminal.

### How to open it

| Computer | What to open |
| --- | --- |
| macOS | Open **Spotlight** (⌘ Space), type `Terminal`, press Enter |
| Windows | Open the Start menu, type `PowerShell`, open **Windows PowerShell** |
| Linux | Open your system’s **Terminal** app |

You type the commands from this page **into that Terminal window**, not into this documentation page.

---

## Before you install

Echo’s installer uses **Python** (version **3.10 or newer**).

In Terminal, check:

```bash
python3 --version
```

On Windows PowerShell, try:

```powershell
python --version
```

You should see a version number like `Python 3.12.x`. If the command fails, install Python 3.10+ from [python.org](https://www.python.org/downloads/), then open a **new** Terminal and try again.

---

## Install Echo (recommended)

These steps use a helper called **pipx**. You do not need to understand pipx in detail. It installs Echo so you can run the `elang` command.

### macOS / Linux

Type these lines **one at a time**, pressing Enter after each:

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

### Open a new Terminal

After `ensurepath`, **close the Terminal and open a new one**. The new window is what picks up the install.

### Check that it worked

In the **new** Terminal:

```bash
elang --version
```

**Success looks like this** (version number may match what you installed):

```text
Echo 2.1.9
```

If you see that line, Echo is installed.

::: tip Command name
The program is named **Echo**. The command you type is **`elang`**. The download package is named **`echolang`**. Docs use `elang`.
:::

### If you see `elang: command not found`

1. Confirm you opened a **new** Terminal after install.
2. Run path setup again, then open another new Terminal:

   ```bash
   python3 -m pipx ensurepath
   ```

   On Windows PowerShell: `python -m pipx ensurepath`

3. Confirm the package is there: `pipx list` should mention `echolang`.

Still stuck? See [Common mistakes](/errors-diagnostics/common-mistakes#elang-command-not-found) for a longer checklist (including PATH details).

---

## Your first Echo file

### 1. Create the file

1. Open a simple text editor (TextEdit on macOS, Notepad on Windows, or any editor you like).
2. Paste this exact line:

```echo
say("Hello, Echo!");
```

3. Save the file as **`hello.echo`**.
4. Remember **which folder** you saved it in (for example, Desktop or Documents).

The `.echo` ending tells you (and Echo) that this file is an Echo program.

### 2. Run it from that folder

In Terminal, go to the folder that contains `hello.echo`.

Examples:

```bash
cd ~/Desktop
```

```powershell
cd $HOME\Desktop
```

Then run:

```bash
elang hello.echo
```

### 3. Expected output

```text
Hello, Echo!
```

If you see that, you ran Echo on your computer.

**Next:** [Lesson 1 — Your first program](/learn/first-program) (explains what each part means).

---

## For people who already develop software

The sections below are optional. Beginners can skip them.

### Install from GitHub without cloning

```bash
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

Same verify → `hello.echo` steps as above.

### Install from a clone (repo root)

`examples/` ships with the git repository only — it is **not** installed by pip/pipx.

```bash
git clone https://github.com/deekshith-poojary98/echo.git
cd echo
pip install .
# or for development: pip install -e .
```

From the **repo root**:

```bash
elang examples/language_feature_smoke.echo
```

### Extra commands

- `elang path/to/file.echo` — run a file
- `elang check [paths...]`
- `elang test [paths...]`
- `elang fmt [paths...] [--check]`
- `elang lint [paths...]`
- `elang builtins` / `elang builtins --count`
- `elang std` / `elang std --exports`
- `elang lsp`

No path on `elang` / `echolang` / `echo` alone starts the REPL (see [CLI and Execution Model](/reference/cli-and-execution-model)).

Optional checks after install:

```bash
elang builtins --count
elang std
```

---

## See also

- [Choose your path](/start/choose-your-path)
- [Lesson 1 — Your first program](/learn/first-program)
- [Common mistakes](/errors-diagnostics/common-mistakes)
- [CLI and Execution Model](/reference/cli-and-execution-model)
