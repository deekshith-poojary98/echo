# Changelog

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
