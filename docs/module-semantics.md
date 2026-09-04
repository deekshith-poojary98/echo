# Echo v0.3 Module Semantics

> **Status:** Frozen language contract
> **Version:** v0.3
> **Implementation status:** Implemented
>
> This document defines the module semantics for Echo v0.3. It is a language contract, not an implementation specification.

`import` is a module-system construct.
`use` / `use mut` remain the existing function mutability and capture construct.

That distinction is part of the contract. It must not be reinterpreted later as “maybe `use` can also load modules.”

---

## 1. Design Goals

Echo v0.3 introduces modules without changing the semantics of existing v0.2.1 programs.

The module system must:

* preserve all existing `use` semantics;
* introduce a separate `import` construct for cross-file dependencies;
* give every `.echo` file its own module scope;
* make exports explicit;
* prevent private names from leaking across module boundaries;
* execute each module at most once per process;
* reject circular dependencies deterministically;
* keep module loading outside the parser and runtime language semantics.

The smallest useful module system is preferred over a feature-rich one.

---

## 2. Module Identity

Every `.echo` file is a module.

There is no special module declaration syntax.

For example:

```text
math.echo
app.echo
```

Both files are modules.

The file supplied to the CLI is simply the **entry module**.

The entry module has no special language semantics beyond being the starting point of execution.

---

## 3. Module Scope

Each module owns an independent module scope.

Names declared in one module are not automatically visible in another module.

For example:

```echo
# math.echo

fn add(a: int, b: int) -> int {
    return a + b;
}

x: int = 10;
```

The names `add` and `x` belong to the `math.echo` module.

Another module cannot access them unless they are explicitly exported and imported.

Module boundaries are therefore real scope boundaries.

---

## 4. Exports

Nothing is exported by default.

A name becomes externally visible only when explicitly marked with `export`.

Example:

```echo
export fn add(a: int, b: int) -> int {
    return a + b;
}

fn subtract(a: int, b: int) -> int {
    return a - b;
}
```

Only `add` is available to importing modules.

`subtract` remains private to its module.

The same rule applies to exported variables:

```echo
export x: int = 10;

y: int = 20;
```

An importing module may access `x`, but not `y`.

Explicit exports are required to prevent accidental API exposure.

---

## 5. Imports

Cross-file dependencies use `import`.

The v0.3 form is:

```echo
import add from "math";
```

This imports the exported name `add` from the module represented by `math.echo`.

Imported names are bound directly into the importer’s module scope.

`import` is a module-scope declaration. All imports in a module are collected during module resolution, before that module’s top-level code executes. An `import` is not a runtime statement that runs in source order.

Example:

```echo
# math.echo

export fn add(a: int, b: int) -> int {
    return a + b;
}
```

```echo
# app.echo

import add from "math";

say(add(2, 3));
```

After the import, `add` is available as a name in `app.echo`.

There is no module namespace:

```echo
math.add(...)
```

is not supported.

Echo currently has no value field-access mechanism, and v0.3 does not introduce one merely to support modules.

---

## 6. Import Selection

Imports are selective.

An import names exactly what it wants to bind:

```echo
import add from "math";
```

This does not import every export from `math.echo`.

If `math.echo` contains:

```echo
export fn add(a: int, b: int) -> int { return a + b; }
export fn multiply(a: int, b: int) -> int { return a * b; }

fn secret() { }
```

then:

```echo
import add from "math";
```

makes only `add` available to the importer.

`multiply` and `secret` are not introduced into the importer’s scope.

---

## 7. `use` Semantics Remain Unchanged

The introduction of modules does **not** change the meaning of `use`.

These forms retain their existing v0.2.1 meaning:

```echo
use name;
use mut name;
```

`use` is a same-module construct related to function capture and mutability.

It is **not** a module-loading mechanism.

In particular:

```echo
use math;
```

does not load `math.echo`.

Cross-file dependencies always use `import`.

This distinction is intentional.

A v0.2.1 program that contains no `import` must retain its existing behavior.

---

## 8. `use mut` Never Crosses a Module Boundary

`use mut` applies only within the current module.

It cannot be used to obtain mutable access to a name owned by another module.

Imported names are never mutable bindings in the importing module.

For example:

```echo
# config.echo

export value: int = 10;
```

```echo
# app.echo

import value from "config";

fn bump() {
    use mut value;
}
```

is invalid.

The imported binding cannot be rebound through `use mut`.

Module boundaries therefore remain stronger than function or block boundaries.

### 8.1 Same-module `use mut` is unchanged (Model A)

v0.3 does **not** give a module’s own functions implicit mutable access to
module-level bindings.

A module-level collection is still an ordinary captured binding:

```echo
export items: list = [];

export fn push_item(value: int) {
    use mut items;
    items.push(value);
}
```

`use mut items;` is required here for the same reason it is required in a
v0.2.1 single-file program.

v0.3 considered and rejected a “module-owned state” exception in which

```echo
items.push(value);
```

would become legal merely because `items` was declared in the same file.
That would be a new mutability rule introduced by modules. v0.3 does not
add that rule.

The two concepts stay separate:

* **binding:** `use mut` is required to mutate a captured name in the
  defining module; imported bindings are never mutable and cannot take
  `use mut`;
* **object:** an imported list or hash may still be mutated because the
  importer holds a reference to the same collection, not because the
  imported name became a mutable binding.

---

## 9. Imported Values

Importing a value does not create a deep copy.

For mutable collections, the imported value refers to the same collection.

For example:

```echo
# data.echo

export values: list = [1, 2, 3];
```

```echo
# app.echo

import values from "data";
```

`values` refers to the exported collection owned by the dependency.

Operations that mutate the collection operate on the shared collection.

This is analogous to passing a mutable list or hash as a function argument.

However, the importer cannot rebind the imported name itself.

The distinction is:

* **binding:** cannot be rebound by the importer;
* **mutable object:** may be mutated according to the normal collection semantics.

---

## 10. Function Imports

Exported functions may be imported like any other exported name.

Example:

```echo
# math.echo

export fn square(x: int) -> int {
    return x * x;
}
```

```echo
# app.echo

import square from "math";

say(square(5));
```

The imported function executes according to normal Echo function semantics.

A function defined in one module does not gain access to the caller’s module locals.

For example:

```echo
# math.echo

export fn read() -> int {
    return secret;
}
```

```echo
# app.echo

secret: int = 42;
import read from "math";

read();
```

`read` cannot see `app.echo`’s `secret`.

Functions retain their definition-site lexical scope.

---

## 11. Private Names

Private module names are inaccessible outside their defining module.

Example:

```echo
# math.echo

secret: int = 42;

export fn answer() -> int {
    return secret;
}
```

An importer can call:

```echo
import answer from "math";
```

but cannot access:

```echo
import secret from "math";
```

because `secret` is not exported.

Private names therefore remain private even when another module depends on the module.

---

## 12. Imported Name Collisions

An imported name is introduced into the importer’s module scope.

Therefore the imported name must not conflict with an existing module-level binding.

For example:

```echo
x: int = 10;

import x from "math";
```

is invalid.

Likewise, importing the same name into the same module more than once is invalid.

The module system does not silently overwrite existing bindings.

---

## 13. Module Resolution

The smallest v0.3 module resolver supports relative module names.

Given:

```text
# project/
#   app.echo
#   math.echo
```

this:

```echo
import add from "math";
```

resolves `math` relative to the importing file:

```text
project/math.echo
```

The `.echo` extension is implied and is not written in the specifier.

The v0.3 specifier is a bare relative name. Given an import from `"math"`, the resolver looks only beside the importing file for `math.echo`.

These specifier forms are not part of v0.3:

* `"math.echo"`
* `"./math"`
* `"../math"`
* subdirectory paths such as `"lib/math"`

The resolver operates on the importing module’s location.

---

## 14. Module Identity

A module’s identity is its resolved absolute path.

Different imports that resolve to the same absolute file identify the same module.

v0.3 has a single specifier form, so this is demonstrated when two modules import the same sibling name and therefore resolve to the same file. Identity is the file, not the specifier string.

Tests must not invent additional specifier spellings, symbolic-link aliases, or extra filesystem names to exercise this rule. Whether two filesystem names that refer to the same inode identify one module is unspecified.

The absolute resolved path is therefore the canonical module identity used for:

* dependency tracking;
* duplicate-import detection;
* cycle detection;
* once-per-process execution.

Module identity is not based on the textual import string alone.

---

## 15. Module Loading and Execution

Modules execute at most once per process.

When the entry module imports another module:

1. the dependency is resolved;
2. its dependencies are loaded first;
3. the dependency’s top-level code executes;
4. its exports become available to the importer;
5. execution continues in the importer.

Example:

```text
app.echo
  └── math.echo
        └── constants.echo
```

Execution order is:

```text
constants.echo
math.echo
app.echo
```

Top-level module code therefore follows dependency-first execution.

---

## 16. Importing the Same Module More Than Once

A module is executed only once per process.

If several modules depend on the same module:

```text
app.echo
├── a.echo
│   └── common.echo
└── b.echo
    └── common.echo
```

`common.echo` executes once.

Its module state is shared by all importers.

The second dependency does not execute the module again.

---

## 17. Entry Module

The file passed to the CLI is the entry module.

For example:

```text
echo app.echo
```

makes `app.echo` the entry module.

The entry module is executed after all of its dependencies have been initialized.

There is no separate `main` module concept in the language.

---

## 18. Circular Imports

Circular dependencies are rejected.

Example:

```echo
# a.echo

import x from "b";
```

```echo
# b.echo

import y from "a";
```

is invalid.

Echo does not expose partially initialized modules.

There is no circular-import recovery mechanism in v0.3.

A cycle is a module-loading error.

---

## 19. No Partial Initialization

A module must complete dependency initialization before it becomes available to its importer.

If initialization fails, the module is not considered successfully initialized.

Importers must not receive a partially initialized module.

This keeps module state deterministic and avoids order-dependent behavior.

---

## 20. Errors

Module-related failures are language/runtime errors with Echo source locations where applicable.

At minimum, v0.3 must distinguish:

* module not found;
* imported name not exported;
* duplicate/conflicting imported binding;
* circular dependency;
* invalid import form.

Python exceptions must not leak through the module boundary.

Diagnostic wording is unspecified. Implementations must distinguish the categories above. Tests must require the category and relevant names, not a particular English phrase.

---

## 21. Semantic Boundaries

The module system does not change the existing lexical-scope rules.

The following remain true:

* a function sees names according to its definition-site scope;
* a caller’s locals are not visible to a callee;
* sibling functions do not share local scope;
* block locals do not leak into their containing scope;
* shadowing does not implicitly write through;
* `use mut` controls mutation only according to existing same-module semantics.

Modules add another lexical boundary above these existing scopes.

Conceptually:

```text
Process
└── Module
    ├── Module scope
    │   ├── Function
    │   │   └── Function scope
    │   └── Block scopes
    └── Imported bindings
```

---

## 22. Pipeline

The language pipeline remains layered.

v0.3 conceptually extends the execution path to:

```text
Source
  ↓
Lexer
  ↓
Tokens
  ↓
Parser
  ↓
Typed AST
  ↓
Semantic Analyzer
  ↓
Module Resolution
  ↓
Module Graph
  ↓
Interpreter
  ↓
Runtime
```

Module loading is not hidden inside the parser.

The parser recognizes the `import` syntax and produces the appropriate AST representation.

Resolution, dependency discovery, cycle detection, loading, and execution ordering belong to the module layer.

---

## 23. Implementation Boundary

The following concepts are expected to exist conceptually:

* module;
* module scope;
* module identity;
* module resolver;
* module dependency graph;
* module loader.

Their exact implementation is deliberately unspecified by this document.

The implementation must preserve the language contract rather than define it.

---

## 24. Explicitly Deferred

The following are intentionally **not** part of v0.3:

### Import aliases

Not supported:

```echo
import add as plus from "math";
```

### Module namespaces

Not supported:

```echo
math.add();
```

### Alternate import specifier spellings

Not part of v0.3:

* an explicit `.echo` suffix in the specifier;
* `./` or `../` prefixes;
* subdirectory or package-like paths;
* extra filesystem names or symbolic links as a way to spell the same module.

### Packages

No package manager or package-resolution semantics.

### Standard-library module paths

No special stdlib import paths.

### Dynamic imports

No runtime/dynamic module loading.

### Circular-import recovery

Cycles are rejected rather than partially initialized.

### Wildcard imports

No:

```echo
import * from "math";
```

### Re-exporting

No module-level mechanism for re-exporting another module’s imports.

These features may be considered later without changing the core v0.3 contract.

---

## 25. Backward Compatibility

A valid v0.2.1 program that contains no `import` must retain its existing semantics.

In particular, v0.3 must not reinterpret:

```echo
use name;
use mut name;
```

as module operations.

Existing function capture, mutability, lexical scoping, runtime values, and error behavior remain governed by the v0.2.1 contract unless explicitly changed by a future language version.

The introduction of modules is additive.

---

## 26. Test Matrix

No module implementation PR is considered valid until the following contract has corresponding tests.

If a test forces a semantic decision this document does not answer, stop and amend the contract first.

### 26.1 Module Identity

* [x] Every `.echo` file is a module
* [x] CLI file is the entry module
* [x] `.echo` extension is implied
* [x] Relative imports resolve beside the importer
* [x] Resolved absolute path defines module identity
* [x] Equivalent paths resolve to one module identity

### 26.2 Exports

* [x] Names are private by default
* [x] `export` makes a name visible to importers
* [x] Private functions cannot be imported
* [x] Private variables cannot be imported
* [x] Multiple exports from one module work

### 26.3 Selective Imports

* [x] `import name from "module"` binds the selected export
* [x] Non-selected exports are not introduced
* [x] Importing an unknown export fails
* [x] Imported names appear in importer module scope
* [x] No namespace access exists

### 26.4 `use` Compatibility

* [x] `use name` retains v0.2.1 behavior
* [x] `use mut name` retains v0.2.1 behavior
* [x] `use` does not load modules
* [x] Existing programs without `import` remain unchanged

### 26.5 Module Scope

* [x] Module-private names are inaccessible to importers
* [x] Importer locals are invisible to imported functions
* [x] Imported functions retain definition-site scope
* [x] Module boundaries prevent accidental name leakage

### 26.6 Mutability

* [x] Imported bindings cannot be rebound
* [x] `use mut` cannot cross a module boundary
* [x] Imported lists share collection identity
* [x] Imported hashes share collection identity
* [x] Mutating an imported collection is visible to other references
* [x] Rebinding an imported collection is rejected

### 26.7 Execution

* [x] Dependencies execute before importers
* [x] Entry module executes last
* [x] A module executes once per process
* [x] Shared dependencies execute once
* [x] Module state is shared across importers
* [x] Top-level code executes exactly once

### 26.8 Cycles

* [x] Direct cycle is rejected
* [x] Indirect cycle is rejected
* [x] Longer dependency cycle is rejected
* [x] No partially initialized module is exposed
* [x] Cycle error identifies the dependency problem

### 26.9 Errors

* [x] Missing module produces an Echo error
* [x] Missing export produces an Echo error
* [x] Invalid import produces an Echo error
* [x] Import collision produces an Echo error
* [x] Circular dependency produces an Echo error
* [x] Python exceptions do not leak

### 26.10 Interaction Tests

The module system must also survive combinations of:

* [x] imported function + closure
* [x] imported function + nested function
* [x] imported function + `use`
* [x] imported function + `use mut`
* [x] imported mutable list + function mutation
* [x] imported mutable hash + function mutation
* [x] multiple importers sharing one mutable export
* [x] nested dependency + closure
* [x] shared dependency imported through two branches
* [x] private module state captured by an exported function
* [x] module initialization failure
* [x] import collision after local declaration
* [x] imported name shadowing inside a function/block
* [x] attempted cross-module `use mut`

The two original interaction tests that omit `use mut` on a defining
module’s own collection encode the rejected Model B shape. They remain
in the suite as a decision record. Model A coverage lives in the
runtime, mutability, and hostile-combination tests: same-module writes
use `use mut`; imported collections are mutated as shared objects.

---

## 27. Implementation Rule

The implementation order for v0.3 is:

```text
Contract
   ↓
Test Matrix
   ↓
Semantic Decisions
   ↓
Resolver Design
   ↓
Module Graph
   ↓
Loader
   ↓
Runtime Integration
```

No implementation should be added merely because it seems like the natural way to make an import statement work.

The implementation exists to satisfy this contract.

---

## 28. v0.3 Definition of Done

The smallest v0.3 module system is complete when:

1. `.echo` files form independent modules.
2. `export` explicitly exposes names.
3. `import name from "module"` selectively binds exports.
4. Imported names flatten into module scope.
5. `use` retains its complete v0.2.1 meaning.
6. `use mut` never crosses a module boundary.
7. Mutable imported collections retain shared identity.
8. Dependencies execute before importers.
9. Each module executes once per process.
10. Module identity is based on resolved absolute path.
11. Circular dependencies are rejected.
12. Private names remain private.
13. Module-related failures produce proper Echo errors.
14. The complete test matrix passes under Model A (`use mut` remains
    the same-module mutability mechanism).
15. Existing v0.2.1 programs without imports remain behaviorally unchanged.

Anything beyond these requirements is outside the smallest v0.3 module system.
