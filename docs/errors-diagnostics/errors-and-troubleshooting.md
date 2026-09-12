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
- list `map` / `filter` callback errors (`E2829`–`E2831`)
- list `reduce` callback errors (`E2832`–`E2834`)
- list `forEach` callback errors (`E2835`–`E2836`)
- list `flatMap` callback errors (`E2837`–`E2839`)
- list `some` / `every` / `findIndex` callback errors (`E2840`–`E2841`; non-`bool` result is `E2831`)
- `chunk()` size errors (`E2842`)
- `rangeList` / `rangeListInclusive` bound errors (`E2843`)
- hash `mapValues` callback errors (`E2844`–`E2845`)
- list `flatten` non-list element errors (`E2846`)
- list `partition` callback errors (`E2847`–`E2848`; non-`bool` result is `E2831`)
- `const` reassignment / mutation (`E3201`–`E3204`)

`fail(message)` always aborts with `message` (code `E2825`). `assert(cond, message)` aborts with the same diagnostic shape when `cond` is falsy (code `E2819`). `expect(cond, message)` requires a `bool` condition (code `E2826`). `expectEq` / `expectNeq` compare with Echo `==` (codes `E2827` / `E2828`).

List `map` / `filter` reject a non-function callback (`E2829`) or a callback that is not exactly one parameter (`E2830`). `filter` also rejects a non-`bool` callback result (`E2831`), including when `filter` is used on a hash. List `reduce` rejects a non-function callback (`E2832`), a callback that is not exactly two parameters (`E2833`), or a callback result whose type does not match `init` (`E2834`). List `forEach` rejects a non-function callback (`E2835`) or a callback that is not exactly one parameter (`E2836`). List `flatMap` rejects a non-function callback (`E2837`), a callback that is not exactly one parameter (`E2838`), or a non-`list` callback result (`E2839`). List `some` / `every` / `findIndex` reject a non-function callback (`E2840`) or a callback that is not exactly one parameter (`E2841`). A non-`bool` callback result uses the same `E2831` as `filter`. `chunk` rejects a `size` that is not an `int` `>= 1` (`E2842`). `rangeList` / `rangeListInclusive` reject bounds that are not convertible to `int` (`E2843`). Hash `mapValues` rejects a non-function callback (`E2844`) or a callback that is not exactly one parameter (`E2845`). List `flatten` rejects a top-level element that is not a `list` (`E2846`). List `partition` rejects a non-function callback (`E2847`) or a callback that is not exactly one parameter (`E2848`). A non-`bool` callback result uses the same `E2831` as `filter`.

`const` reassignment (`x =`, `x +=`) is **E3201**. In-place mutation through a const name (`push`, index assign, hash field set) is **E3202**. Mutating a frozen list or hash through another name or a function parameter is **E3203**. `use mut` on a const binding is **E3204**.

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
