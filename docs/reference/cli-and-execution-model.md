# CLI and Execution Model

## Overview
Echo source files are tokenized, parsed, and interpreted at runtime.

## Syntax
```bash
python src/main.py file.echo
python src/main.py file.echo --plain
```

## How Echo Runs
1. Lexer reads the source file and produces tokens
2. Parser turns tokens into an AST
3. Interpreter executes the AST directly

## CLI
### Run a file
```bash
python src/main.py program.echo
```

### Plain output mode
```bash
python src/main.py program.echo --plain
```

Use plain mode when you want simple text output without Rich panels.

### Analyze without running
```bash
echo check program.echo
echo check program.echo --plain
```

`check` lexes, parses, and analyzes the file and its import graph. It does not execute. Success prints nothing and exits 0. Failures use the same diagnostics as a normal run. The first argument must be the word `check`; `echo check.echo` still runs a file named `check.echo`.

### REPL
```bash
echo
echo --plain
```

With no source file, Echo starts a REPL. `--plain` uses the same plain diagnostics as file runs.

Each submission is a complete program (names do not persist across prompts). A submission can span lines: Echo keeps reading while `{` is unclosed, or while a triple-quoted string is unterminated, and shows `... ` until the input is complete. A one-line `if true { say(1); }` works. Put a function and a call in the same submission if you need both.

Empty lines at a fresh `echo> ` prompt are ignored. A syntax, semantic, or runtime error prints an Echo diagnostic and returns to the prompt; it does not kill the process or print a Python traceback.

Quit with `exit(code)` (the process returns that code) or EOF (Ctrl-D), which exits 0. Ctrl-C cancels the current submission and returns to `echo> `.

### Run as a test
```bash
echo test program.echo
echo test program.echo --plain
```

Runs the file, including imported modules. Exit 0 is pass (`exit(0)` in the file is also pass). Any other process code — including `exit(2)` — is a failed test. Semantic and runtime failures print an Echo diagnostic and exit non-zero. A missing file exits non-zero with `source file not found`. `echo test` with no path prints help and exits 2. Program stdout is shown (the runner is not silent). There is no test DSL. The first argument must be the word `test`; `echo test.echo` still runs a file named `test.echo`.

## Notes
- The file passed to the CLI is the entry module when it contains `import`.
- Errors are reported by category: syntax, semantic, name, type, argument, index, mutation, or execution.

## See Also
- [Quick Start](/getting-started/quick-start)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
- [Known Limitations](/errors-diagnostics/known-limitations)
