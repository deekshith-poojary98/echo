# Quick Start

Write a file, run it. That is the whole page.

## Hello

Create `hello.echo`:

```echo
say("Hello, Echo!");
```

```bash
elang hello.echo
```

Output:

```text
Hello, Echo!
```

Plain diagnostics (no Rich panels):

```bash
elang hello.echo --plain
```

On aborts inside a call, `--plain` may show a doubled `Stack: Stack:` header — a known quirk. Details: [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting#plain-mode-stack-header).

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

- [Playground](/playground) — browser demo; files / `run` / HTTP are denied there (**E2801**); `std/…` imports work
- [Installation](/getting-started/installation)
- [Mini Programs](/examples/mini-programs) — includes nested modules + `std/…` demos
- [Getting Started / Language Tour](/getting-started/tour)
- [Syntax Basics](/getting-started/syntax-basics)
- [Variables and Types](/getting-started/variables-and-types)
