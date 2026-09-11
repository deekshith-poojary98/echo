# Changelog

## 0.5.8

A small `echo lint` rule expansion. Same finding format. Not a second typechecker.

- New rules: `test-naming` (top-level `fn` that looks like a test but is not a zero-arg `testXxx` unit), `self-assign` (`x = x` / `x = x + 0` / `x = 0 + x`), and `unreachable-after-fail` (later statements in the same block after `fail(...)` or `return`)
- Unused parameters stay `unused-local`; there is no separate `unused-param` rule
- `unused-export` is not shipped: exports are for other files, and Echo has no file-local convention that would distinguish a dead export from a library API
- `redundant-parens` is not shipped: the parser drops grouping parentheses, so the AST cannot see what the formatter would omit
- Findings still print `path:line:col: rule: message`. Matcher `$echo-lint` is unchanged

## 0.5.7

Editor integration for the fmt / lint / test / check CLI (not an LSP).

- The VS Code / Cursor extension `echo-syntax-highlighter/` contributes tasks, problem matchers, and commands that run `echolang check` / `fmt` / `lint` / `test` with `--plain` so diagnostics land in the Problems panel
- Matchers cover `Error[E####]` / `Error:` plus `--> file:line:col` (check and parse errors), lint `path:line:col: rule: message`, and `echo test` failures that include a location
- Format Document shells out to `echolang fmt`; this is not a language server, completions, or jump-to-definition
- Install the Echo CLI (`echolang` on PATH). The Unix `echo` builtin is not the language

## 0.5.6

Native `echo test` product: expect-style helpers, file and function units, pass/fail summary. No new keywords. No `test "name" { }` syntax.

- `echo test [paths...]` runs files or recursively discovers `*_test.echo` in directories. Explicit file paths always run, even if they are not named `*_test.echo`. No path prints help and exits 2
- Zero-argument top-level `fn testXxx()` functions are separate units (Go-shaped). Other top-level statements run once as setup, or as the file unit when there are no `test*` functions
- `expect(cond, message)`, `expectEq(left, right, message)`, and `expectNeq(left, right, message)` record a failure and continue under `echo test`. Outside a test run they abort like `assert`. `cond` must be `bool`. Codes **E2826** / **E2827** / **E2828**
- `assert` / `fail` still abort the current unit. Later units still run. The runner exits 0 if every unit passed and 1 if any failed (including `exit(n)` with n ≠ 0)
- Summary lines look like `ok   path/foo_test.echo::testAdd` / `FAIL path/foo_test.echo::testSub` then `N passed, M failed`
- The first argument must be the word `test`; `echo test.echo` still runs a file named `test.echo`

## 0.5.5

`fail(message)` and `echo lint`. No new syntax. No `try` / `catch`.

- `fail(message)` always aborts with an Echo error; `message` must be `str`. Not recoverable. No `*Or` twin. Error code **E2825**
- `echo lint [paths...]` reports style findings without running the program: unused locals/functions/imports, comparison to boolean literals, redundant `by 1`, empty if/function bodies, and names that shadow builtins
- Dirty lint findings print `path:line:col: rule: message` and exit 1; a clean tree exits 0
- A directory argument lints `*.echo` recursively; parse errors use the same diagnostic as `echo check`; no path prints help and exits 2
- The first argument must be the word `lint`; `echo lint.echo` still runs a file named `lint.echo`. `fail` is a builtin, not a CLI command, so `echo fail.echo` still runs that file

## 0.5.4

Canonical `echo fmt`. No language change.

- `echo fmt [paths...]` rewrites Echo sources in place: 4-space indent, comments kept, `else if` flattening, parentheses from operator precedence
- `echo fmt --check` prints paths that would change and exits 1; already-formatted files exit 0
- A directory argument formats `*.echo` files recursively; no path prints help and exits 2
- Parse errors print the same diagnostic as `echo check` and do not write a broken file
- The first argument must be the word `fmt`; `echo fmt.echo` still runs a file named `fmt.echo`
- Number literals may be respelled (`1e3` → `1000.0`); strings are wrapped from raw lexemes and are not re-escaped

## 0.5.3

Fallback `*Or` twins for untrusted input. Aborting originals are unchanged. No `try` / `catch`. No `Result` type.

- `readFileOr(path, fallback)` returns file text on success and `fallback` for missing files, invalid UTF-8, directories, and other read OS errors
- Restricted hosts still deny `readFileOr` with E2801; a non-string path is still a type error
- `parseJsonOr(text, fallback)` returns the parsed value or `fallback` for invalid JSON; non-string text is still a type error
- `asIntOr(value, fallback)` / `asFloatOr(value, fallback)` return the converted number or `fallback` for unparseable strings, `null`, lists, and hashes
- `asIntOr(true, 0)` / `asFloatOr(true, 0.0)` stay type errors — bool has no twin
- `readFile`, `parseJson`, `asInt`, and `asFloat` still abort

## 0.5.2

REPL session state. One `echo` process keeps one environment for the lifetime of the REPL.

- Bindings, functions, and type aliases persist across submissions; builtins stay available
- Analyzer scope is seeded from prior successful submissions so later snippets can use earlier names
- A failed lex/parse/semantic/runtime submission does not drop earlier bindings; analyze failures are not executed
- A runtime error does not roll back the interpreter: `x: int = 1; bad();` may leave `x` assigned even though that submission failed
- `import` in the REPL loads sibling `.echo` files from the working directory into the session
- `use mut` works for variables declared earlier in the session
- `exit(code)`, EOF, `--plain`, and brace/triple continuation are unchanged

## 0.5.1

Harden the 0.5.0 CLI and restricted host. No new language features.

- REPL continues while `{` is unclosed and while a triple-quoted string is unterminated
- Empty REPL lines are ignored; `exit(code)` and EOF (Ctrl-D) leave without a Python traceback
- A failed REPL submission returns to the prompt instead of killing the process
- `echo test` with no path prints help and exits 2; `exit(2)` in a test file is a failed test; imports execute
- `Host.run_process` refuses to launch when `allow_run=False` (playground policy)

## 0.5.0

Language basics. Syntax and stdlib together: this is **0.5.0** because multiline strings and `.5` / scientific number literals change the grammar. Builtins-only would have been 0.4.4.

- `assert(cond, message)` aborts with an Echo error when `cond` is falsy; `message` must be `str`
- `copyFile(src, dest)` binary-copies a file; restricted hosts deny it
- `pathJoin(...)` joins 2+ path parts with pathlib; available in the playground
- `run(command, args)` runs a process without a shell and returns `{ code, stdout, stderr }`; `Host.allow_run` defaults true; playground sets `allow_run=False`
- `now()` returns unix time as `int` seconds
- `random()` is a float in `[0, 1)`; `randomInt(min, max)` is inclusive
- Triple-quoted `"""` / `'''` strings may span lines and still interpolate `${...}`
- Number literals `.5`, `1e3`, and `1e-3`; `5.` stays integer-then-dot
- `readLine()` reads one stdin line; EOF aborts
- `echo` with no file starts a REPL (`--plain` supported)
- `echo test path.echo` runs a file; exit 0 is pass

## 0.4.3

Host and stdlib depth. No new syntax.

- `mkdir(path)` creates the leaf directory only; missing parent, existing path, and a file in the way abort
- `removeFile(path)` deletes a file; missing paths and directories abort
- Restricted hosts deny `mkdir` and `removeFile` the same way they deny `readFile`
- String `indexOf` / `lastIndexOf` (missing → `-1`; empty part → `0` / length)
- String `repeat`, `padStart` / `padEnd`, and `replaceFirst`
- Numeric `abs`, `min(a, b)`, `max(a, b)`, `floor`, and `ceil` (reject `bool`)
- `eprint(...)` writes to stderr the same way `say` writes to stdout

## 0.4.2

Host completeness for scripts. No new syntax.

- `cwd()` returns the host working directory as a string
- `exit(code)` stops the program with that process code and no error diagnostic
- `isDir(path)` returns `bool` and does not abort when the path is missing
- `listFiles(path)` returns sorted directory entry names; missing paths and files abort
- Restricted hosts deny `isDir` and `listFiles` the same way they deny `readFile`

## 0.4.1

Stdlib and tooling depth. No new syntax.

- `join(separator)` on a list of strings
- `startsWith` / `endsWith` on strings
- `fileExists(path)` returns `bool` and does not abort when the file is missing
- `echo check file.echo` analyzes without executing
- Restricted hosts still deny `fileExists` the same way they deny `readFile`

## 0.4.0

Host and standard-library cut. No new syntax.

- `args()`, `env()`, `envOr()`, `readFile()`, `writeFile()`, `parseJson()`, `writeJson()`
- String/list `split`, `replace`, `contains`, `slice`; hash `has`
- `asInt` / `asFloat` reject `bool` (semantic correction)
- Failures still abort with Echo errors; playground denies files
- Not included: slice syntax, `try/catch`, function values, classes

## 0.3.0

File-based modules on top of the frozen v0.2.1 language.

- `import name from "module"` and `export` are the only module syntax
- Sibling `.echo` files resolve by bare name; `.echo` is implied
- Exports are explicit; imports are selective and flatten into module scope
- Imported bindings are immutable; imported collections share identity
- `use` / `use mut` keep their v0.2.1 meaning and never load modules
- Same-module writes still require `use mut` (no module-owned-state exception)
- Circular dependencies are rejected before any module initializes
- A program with no `import` keeps the single-file pipeline

## 0.2.1

Semantic cleanup under the frozen v0.2 pipeline.

- User-function keyword arguments are validated by the semantic analyzer
- Builtin arity checks for required standalone calls
- `foreach` only accepts lists and hashes
- `for` bounds reject `bool` and other non-numeric values
- `order()` of mixed types is an Echo type error
- Index assignment uses Echo index errors, not Python exceptions
- Error categories distinguish argument, index, and mutation errors

## 0.2.0

Architecture and correctness release.

- Documented language semantics
- Typed AST, semantic analyzer, and split runtime
- Lexical scoping and nested-block `use mut`
- Distinct `null` lookup and `bool` vs `int`
- Source locations and Echo error types
- Builtins removed from the lexer
- CLI `--version`
- Correctness fixes for comments, interpolation, `reverse`, `find`, `format`, `wait`, and `asInt`
