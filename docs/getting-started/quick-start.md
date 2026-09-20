# Quick Start

Write a file, run it. That is the whole page.

## Hello

Create `hello.echo`:

```echo
say("Hello, Echo!");
```

From a clone of this repo:

```bash
python src/main.py hello.echo
```

If Echo is installed (`elang`):

```bash
elang hello.echo
```

Output:

```text
Hello, Echo!
```

Plain diagnostics (no Rich panels):

```bash
python src/main.py hello.echo --plain
```

## Rules you hit immediately

- Statements end with `;`.
- Blocks use `{ }`. Newlines do not end statements.
- Indentation is not syntax (unlike Python).

Wrong:

```echo
say("Hello, Echo!")
```

Right:

```echo
say("Hello, Echo!");
```

## Next

- [Playground](/playground)
- [Installation](/getting-started/installation)
- [Getting Started / Language Tour](/getting-started/tour)
- [Syntax Basics](/getting-started/syntax-basics)
- [Variables and Types](/getting-started/variables-and-types)
