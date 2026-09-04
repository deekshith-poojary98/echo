# Echo Architecture (v0.2)

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

## Package layout

```text
src/echo/
  cli/          program entry
  frontend/     tokens, lexer, parser, AST
  semantics/    scopes, symbols, validation
  runtime/      execution
  core/         list / hash / string operations
```

## Rules

- The lexer does not know about builtins, scopes, or types beyond language keywords.
- The parser produces typed AST nodes, not dictionaries.
- Semantic analysis answers “what does this name mean?”
- Runtime context answers “what value does it hold?”
- Builtins live in `runtime/builtins.py` and `core/`.
- All failures are `EchoError` subclasses.
