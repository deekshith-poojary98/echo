# Echo

Echo is a small interpreted scripting language. Types are declared explicitly and checked at runtime. Abort is the default failure mode; recovery is inquiry and `*Or` twins, not `try` / `catch`.

Docs: [https://deekshith-poojary98.github.io/echo/](https://deekshith-poojary98.github.io/echo/) — includes a [browser playground](https://deekshith-poojary98.github.io/echo/playground).

```echo
name: str = "Echo";
scores: list = [95, 85, 75];

fn greet(name: str) -> void {
    say("Hello, ${name}!");
}

greet(name);

for i: int in 0..10 by 2 {
    say("Count:", i);
}
```

## What you get

- Typed declarations and parameters; runtime checks on bind / assign / return
- `list` and `hash`, string interpolation, method calls, `use mut`, lexical scope
- File modules: `export` / `import name from "module"`
- Type aliases, object types (`exact { ... }` too), unions (`int | str`), first-class functions and builtins-as-values
- Nominal `class` with `new { ... }` fields, methods (`this`), type methods, unbound methods, and `interface` (optional `implements`; no inheritance)
- CLI: run a file, REPL, `check`, `test`, `fmt`, `lint`

## What you do not

- No class inheritance (`extends`), no generics, no `try` / `catch`
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
- `docs/` — VitePress site (this is the docs source)
- `docs/language-semantics.md` — language contract (v0.2 base; additive through 1.0.0)
- `docs/module-semantics.md` — v0.3 module contract
- `*.echo` / `examples/` — sample programs (including `examples/classes_and_interfaces.echo`)

## License / contributing

License and contribution guidelines are not filled in yet.
