# Quick Start

## Overview
This page gets you from zero to a running Echo file as quickly as possible.

## Syntax
```echo
say("Hello, Echo!");
```

## Example
Create a file named `hello.echo`:

```echo
say("Hello, Echo!");
```

Run it:

```bash
python src/main.py hello.echo
```

## Output
```text
Hello, Echo!
```

## Notes
- Echo runs source files through the Python interpreter entry point in `src/main.py`.
- Add `--plain` if you want plain-text errors and warnings.

```bash
python src/main.py hello.echo --plain
```

- Statements end with `;`.
- Blocks use ``{}``.
- Newlines do not end statements.

## Common Mistakes
### Forgetting the semicolon
```echo
say("Hello, Echo!")
```

Use:

```echo
say("Hello, Echo!");
```

### Expecting Python indentation rules
Echo does not use indentation to define blocks.

## Next Steps
- [Getting Started](/getting-started/getting-started)
- [Syntax Basics](/getting-started/syntax-basics)
- [Variables and Types](/getting-started/variables-and-types)
