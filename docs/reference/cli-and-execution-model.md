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

With no source file, Echo starts a REPL. Each line is a complete program. `--plain` uses the same plain diagnostics as file runs. `exit(code)` leaves the REPL with that process code.

### Run as a test
```bash
echo test program.echo
echo test program.echo --plain
```

Runs the file. Exit 0 is pass. There is no test DSL. The first argument must be the word `test`; `echo test.echo` still runs a file named `test.echo`.

## Notes
- The file passed to the CLI is the entry module when it contains `import`.
- Errors are reported by category: syntax, semantic, name, type, argument, index, mutation, or execution.

## See Also
- [Quick Start](/getting-started/quick-start)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
- [Known Limitations](/errors-diagnostics/known-limitations)
