# Echo Architecture

Pipeline as of the v0.2 layout (modules sit between analyzer and runtime; see `module-architecture.md`).

```text
Source
  → Lexer          (frontend)
  → Tokens
  → Parser         (frontend)
  → Typed AST
  → Analyzer       (semantics)
  → Interpreter    (runtime)
       → Context / Values / Functions / Operators / Builtins
```

With `import`: resolver → module graph → loader wrap the same analyzer/interpreter per file. A program with no `import` never builds a module graph.

## Package layout

```text
src/echo/
  cli/          program entry (run, REPL, check, fmt, lint, test)
  frontend/     tokens, lexer, parser, AST
  semantics/    scopes, symbols, validation
  modules/      resolve, graph, load
  runtime/      execution
  core/         list / hash / string operations
```

## Rules

- The lexer does not know about builtins, scopes, or types beyond language keywords.
- The parser produces typed AST nodes, not dictionaries.
- Semantic analysis answers “what does this name mean?”
- Runtime context answers “what value does it hold?”
- Builtins live in `runtime/builtins.py` and `core/`.
- Failures are `EchoError` subclasses — not leaked Python exceptions.
