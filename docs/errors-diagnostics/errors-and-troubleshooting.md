# Errors and Troubleshooting

Errors carry a category and usually a hint. Abort is the default; see [failure model](/failure-model).

## Categories

### Syntax

Missing `;`, `)`, `]`, `}`, or malformed function / loop syntax.

### Name

Undeclared or out-of-scope name; missing `use` / `use mut`; undefined function.

### Type

Wrong assign / argument / return type; builtin called on the wrong kind of value.

### Execution

Runtime failures that still abort as Echo errors:

- List index out of range; missing hash key; bad method use; invalid `format()` placeholder
- `assert` / `fail` abort (`E2819` / `E2825`)
- `expect` / `expectEq` / `expectNeq` abort outside `echo test` (`E2826` / `E2827` / `E2828`); under `echo test` they record and continue
- List `map` / `filter` callback errors (`E2829`–`E2831`)
- List `reduce` (`E2832`–`E2834`); `forEach` (`E2835`–`E2836`); `flatMap` (`E2837`–`E2839`)
- List `some` / `every` / `findIndex` (`E2840`–`E2841`; non-`bool` result is `E2831`)
- `chunk()` size (`E2842`); `rangeList` / `rangeListInclusive` bounds (`E2843`)
- Hash `mapValues` (`E2844`–`E2845`); list `flatten` (`E2846`); list `partition` (`E2847`–`E2848`; non-`bool` is `E2831`)
- Host deny for files / run / HTTP (`E2801`)
- Regex builtins (`E2850`); date helpers (`E2851`); HTTP (`E2852`); URL helpers (`E2853`); Base64 helpers (`E2854`)
- `const` reassignment / mutation (`E3201`–`E3204`)
- Destructuring length / shape (`E3205`–`E3207`); missing hash keys reuse **E2711**
- Exact object shape: extra field **E3208**, missing field **E3209**
- Non-exhaustive `switch` without `else` (**E3210**)

## Codes worth knowing

`fail(message)` always aborts (`E2825`). `assert(cond, message)` aborts when `cond` is falsy (`E2819`). Same diagnostic shape.

`expect(cond, message)` requires a `bool` (`E2826`). `expectEq` / `expectNeq` use Echo `==` (`E2827` / `E2828`).

Host / scripting stdlib:

| Code | Surface |
| --- | --- |
| `E2801` | Host deny — `allow_files=False` / `allow_run=False` / `allow_http=False` |
| `E2850` | Regex builtins — bad types or invalid pattern |
| `E2851` | Date helpers — bad types or invalid format / parse |
| `E2852` | HTTP — bad types, empty URL, network / timeout / invalid URL (non-2xx still returns the response hash) |
| `E2853` | URL helpers — bad types (`urlEncode` / `urlDecode` / `urlJoin` / `urlQuery`) |
| `E2854` | Base64 helpers — bad types or invalid Base64 text |

`httpGetOr` / `httpPostOr`: network / empty-URL **E2852** runtime failures return `fallback`; type errors and host deny (**E2801**) still abort.

List HOF callbacks:

| Family | Non-function | Arity | Other |
| --- | --- | --- | --- |
| `map` / `filter` | `E2829` | unary → `E2830` | non-`bool` from `filter` → `E2831` (also hash `filter`) |
| `reduce` | `E2832` | not binary → `E2833` | result type ≠ `init` → `E2834` |
| `forEach` | `E2835` | not unary → `E2836` | |
| `flatMap` | `E2837` | not unary → `E2838` | non-`list` result → `E2839` |
| `some` / `every` / `findIndex` | `E2840` | not unary → `E2841` | non-`bool` → `E2831` |
| `partition` | `E2847` | not unary → `E2848` | non-`bool` → `E2831` |
| hash `mapValues` | `E2844` | not unary → `E2845` | |

`chunk` size not an `int` `>= 1` → `E2842`. `rangeList` / `rangeListInclusive` non-int bounds → `E2843`. `flatten` top-level non-list → `E2846`.

`const`: reassignment **E3201**; mutate through the const name **E3202**; mutate a frozen value via another name / parameter **E3203**; `use mut` on const **E3204**.

Destructuring: length mismatch **E3205**; list pattern on non-list **E3206**; hash pattern on non-hash **E3207**. Missing hash keys → **E2711**. Exact extras / missing → **E3208** / **E3209**.

`for` / range `by 0` → **E2702** (also non-convertible range bounds).

## Lint is not a runtime error

`echo lint` prints `path:line:col: rule: message` and exits 1 on findings. Rules: `unused-local`, `unused-function`, `unused-import`, `comparison-to-bool`, `redundant-by-one`, `empty-block`, `shadow-builtin`, `test-naming`, `self-assign`, `unreachable-after-fail`. Zero-arg `fn test*` is not unused-function. `test-naming` flags a top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit.

## Example

```echo
count = 1;
```

Name error: `count` was never declared.

## Notes

- Non-plain mode: some errors/warnings use Rich panels.
- `--plain`: simple text.
- Hints are printed for common mistakes.

## Common Fixes

- Declare before assign
- Add the missing semicolon
- Add `use` or `use mut` inside functions
- Check list indexes and hash keys
- Match declared types

## See Also

- [Scope, use, and watch](/core-concepts/scope-use-watch)
- [CLI and Execution Model](/reference/cli-and-execution-model)
- [Known Limitations](/errors-diagnostics/known-limitations)
