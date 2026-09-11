# Change Log

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
