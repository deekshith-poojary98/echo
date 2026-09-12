# Change Log

## 0.7.1

- Version tracks Echo v0.7.1.
- Sample highlights list/hash destructuring, rest, and destructuring parameters.

## 0.7.0

- Version tracks Echo v0.7.0.
- `const` is highlighted as a keyword (`storage.modifier`).

## 0.6.9

- Version tracks Echo v0.6.9.
- Builtin highlighting includes `flatten` and `partition`.

## 0.6.8

- Version tracks Echo v0.6.8.
- Builtin highlighting includes `chunk`, `rangeList`, `rangeListInclusive`, and `mapValues`.

## 0.6.7

- Version tracks Echo v0.6.7.
- Builtin highlighting includes `zip` and `unique`.

## 0.6.6

- Version tracks Echo v0.6.6.
- Sample highlights optional slice bounds `xs[1:]` / `xs[:4]` / `xs[:]`. Colon and brackets stay punctuation (same as `xs[1:4]`).

## 0.6.5

- Version tracks Echo v0.6.5.
- Builtin highlighting includes `some`, `every`, and `findIndex`.
- Grammar sync also checks the playground CodeMirror `BUILTINS` list.

## 0.6.4

- Version tracks Echo v0.6.4.
- Builtin highlighting includes `flatMap`.

## 0.6.3

- Version tracks Echo v0.6.3.
- Builtin highlighting includes `forEach`.

## 0.6.2

- Version tracks Echo v0.6.2.
- Builtin highlighting includes `reduce`.

## 0.6.1

- Version tracks Echo v0.6.1.
- Builtin highlighting includes `map` and `filter`.

## 0.6.0

- Version tracks Echo v0.6.0.
- Grammar already highlighted `fn` and `...`; lambdas `fn(...)`, function types `fn(int) -> int`, slice `xs[1:4]`, and `name: T = expr` / `name: T...` use those tokens.

## 0.5.9

- Version tracks Echo v0.5.9.
- **Echo: Check workspace** runs `echolang check --plain` on `${workspaceFolder}` with the `$echo` matcher. **Echo: Check file** is unchanged.

## 0.5.8

- Version tracks Echo v0.5.8. No grammar or builtin changes.

## 0.5.7

- Editor integration (not an LSP): tasks, problem matchers, and Problems panel wiring for `echolang check` / `fmt` / `lint` / `test`.
- Commands: Echo: Check file, Lint, Format, Test. Format Document shells out to `echolang fmt`.
- Snippets for `fn testName()`, `expect` / `expectEq`, and `fail`.
- Grammar still matches Echo v0.5.6 language surface; no new keywords.

## 0.5.6

- Grammar matches Echo v0.5.6, including `expect` / `expectEq` / `expectNeq`.

## 0.5.5

- Grammar matches Echo v0.5.5, including `fail(message)`.
- Builtin calls use a distinct scope, including `assert`, `*Or` twins, and host/stdlib names from 0.4–0.5.x.
- Strings highlight `${...}` interpolation; numbers match `.5` and scientific literals.
- Removed tokens Echo does not have (`as` keyword, hex/binary literals).
- README covers install in VS Code / Cursor and how to update the builtin list.

## 0.0.1

- Initial TextMate grammar stub.
