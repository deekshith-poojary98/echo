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

## Notes
- Echo currently runs one source file at a time.
- There is no Echo module/import system yet.
- Errors are reported by category: syntax, name, type, or execution.

## See Also
- [Quick Start](/getting-started/quick-start)
- [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
- [Known Limitations](/errors-diagnostics/known-limitations)
