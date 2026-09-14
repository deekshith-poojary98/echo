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

If Echo is installed (`echolang`):

```bash
echolang hello.echo
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

- [Playground](/playground) — run in the browser
- [Installation](/getting-started/installation)
- [Getting Started](/getting-started/getting-started)
- [Syntax Basics](/getting-started/syntax-basics)
- [Variables and Types](/getting-started/variables-and-types)
