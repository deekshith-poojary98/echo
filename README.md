# Echo

Echo is a small interpreted scripting language. Types are declared explicitly and checked at runtime. Abort is the default failure mode; recovery is inquiry and `*Or` twins, not `try` / `catch`.

Docs: [https://deekshith-poojary98.github.io/echo/](https://deekshith-poojary98.github.io/echo/) — includes a [browser playground](https://deekshith-poojary98.github.io/echo/playground).

```echo
import add from "lib/math";
import stdOk from "std/meta";

say("2+3 =", add(2, 3));
say("std ready:", stdOk());
```

**2.0** is path resolution + std modules — nested / relative imports and `import … from "std/…"`. It is **not** a package manager (no registry, lockfiles, or `elang add`).

## What you get

- Typed declarations and parameters; runtime checks on bind / assign / return
- `list` and `hash`, string interpolation, method calls, `use mut`, lexical scope
- File modules: `export` / `import name from "module"` (sibling, `./…`, `../…`, nested `"lib/math"`, reserved `"std/…"`)
- Type aliases, object types (`exact { ... }` too), unions (`int | str`), first-class functions and builtins-as-values
- Nominal `class` with `new { ... }` fields, methods (`this`), type methods, unbound methods, and `interface` (optional `implements`; no inheritance)
- Thin scripting stdlib via prelude and/or `std/…` (`std/fs`, `std/json`, `std/os`, `std/re`, `std/time`, `std/http`, `std/url`, `std/base64`, `std/yaml`); optional `--require-std` hides peeled prelude names; host-gated where noted
- CLI: run a file, REPL, `check`, `test`, `fmt`, `lint`, `builtins`, `std`, `lsp`

## What you do not

- No class inheritance (`extends`), no generics, no `try` / `catch`, no package registry
- Type inference is limited — you still declare types
- See [Known Limitations](https://deekshith-poojary98.github.io/echo/errors-diagnostics/known-limitations) and [failure model](https://deekshith-poojary98.github.io/echo/failure-model)

## Install

Python 3.10+. Prefer the command name **`elang`** — short, and shells often reserve `echo`. The package also registers `echolang` (and `echo`).

Package name on PyPI is **`echolang`**.

### pipx (recommended)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install echolang
elang --version
elang builtins --count
elang std
elang std --exports
```

From GitHub instead of PyPI:

```bash
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

### From a clone

```bash
pip install .
# or: pip install -e .
elang path/to/file.echo
```

## Layout

- `src/echo/` — frontend, semantics, modules, runtime, CLI
- `src/echo/std/` — install-tree modules for `import … from "std/…"`
- `docs/` — VitePress site (this is the docs source)
- `docs/language-semantics.md` — language contract (v0.2 base; additive through **2.0.x**)
- `docs/module-semantics.md` — v0.3 module contract (+ **2.0** path / std notes)
- `docs/reference/builtin-inventory.md` — generated prelude list
- `docs/reference/std-inventory.md` — generated `std/…` modules + exports (`python tools/sync_builtins.py`)
- `examples/` — sample programs (`std_imports.echo`, `modules_demo/`, …)

## License / contributing

License and contribution guidelines are not filled in yet.
