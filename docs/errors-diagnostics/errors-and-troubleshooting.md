# Errors and Troubleshooting

## Overview
Echo reports errors by category and usually includes a helpful hint.

## Error Categories
### Syntax Error
Common causes:
- missing `;`
- missing `)`
- missing `]`
- missing `}`
- malformed function or loop syntax

### Name Error
Common causes:
- variable not declared
- variable not visible in current scope
- missing `use` or `use mut`
- undefined function

### Type Error
Common causes:
- assigning wrong type to a declared variable
- wrong function argument type
- wrong return type
- calling a built-in on the wrong kind of value

### Execution Error
Common causes:
- list index out of range
- missing hash key
- invalid method usage
- invalid `format()` placeholder
- `assert` / `fail` abort (`E2819` / `E2825`)
- `expect` / `expectEq` / `expectNeq` abort outside `echo test` (`E2826` / `E2827` / `E2828`); under `echo test` they record and continue

`fail(message)` always aborts with `message` (code `E2825`). `assert(cond, message)` aborts with the same diagnostic shape when `cond` is falsy (code `E2819`). `expect(cond, message)` requires a `bool` condition (code `E2826`). `expectEq` / `expectNeq` compare with Echo `==` (codes `E2827` / `E2828`).

`echo lint` is not an Echo runtime error. Findings print `path:line:col: rule: message` and exit 1. Rules: `unused-local`, `unused-function`, `unused-import`, `comparison-to-bool`, `redundant-by-one`, `empty-block`, `shadow-builtin`, `test-naming`, `self-assign`, `unreachable-after-fail`. Zero-arg `fn test*` functions are not unused-function. `test-naming` flags a top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit.

## Example
```echo
count = 1;
```

Typical result: a name error because `count` was never declared.

## Notes
- In non-plain mode, some errors and warnings use Rich panels.
- In plain mode, errors print as simple text.
- The interpreter also prints hints for common mistakes.

## Common Fixes
- Declare variables before assignment
- Add the missing semicolon
- Add `use` or `use mut` inside functions
- Check list and hash indexes
- Match declared types

## See Also
- [Scope, use, and watch](/core-concepts/scope-use-watch)
- [CLI and Execution Model](/reference/cli-and-execution-model)
- [Known Limitations](/errors-diagnostics/known-limitations)
