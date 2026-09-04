# Echo v0.3 Module Architecture

> **Status:** Architecture
> **Version:** v0.3 design
> **Implementation status:** Not implemented
>
> This document defines component boundaries for the v0.3 module system.
> It does not change language semantics. The language contract remains
> `docs/module-semantics.md`.

> **`import` is a module-system construct. `use` / `use mut` remain function mutability and capture.**

`use` never enters the resolver, the graph, or the loader.
A program that contains no `import` never constructs a module graph.

---

## 1. Purpose

The architecture exists so implementation cannot invent language behavior.

`module-semantics.md` says what Echo does.
This document says which component is allowed to do it.

If a behavior cannot be placed in one of the components below, it is not a v0.3 feature.

---

## 2. Pipeline

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST                         import / export nodes only
  ↓
ModuleResolver              path → canonical file
  ↓
ModuleGraph                 dependencies, cycles, order
  ↓
Semantic Analyzer           names, exports, collisions
  ↓
ModuleLoader                once-per-process initialization
  ↓
Interpreter                 module scopes and imported bindings
```

The parser recognizes `import` and `export` syntax and produces AST.
It does not resolve files, load dependencies, or execute modules.

Resolution, graph construction, cycle detection, loading, and execution
ordering belong to the module layer.

`use` / `use mut` remain ordinary function-scope constructs. They are
analyzed and executed by the existing semantic analyzer and interpreter.

---

## 3. Module Representation

A module is one `.echo` file.

There is no module declaration syntax. The file is the module.

Each module record holds:

| Field | Meaning |
|---|---|
| canonical path | resolved absolute path; the module identity |
| AST | parsed program of that file |
| module scope | names declared in this file, plus imported bindings |
| exports | names explicitly marked `export` |
| dependencies | canonical paths this module imports |
| initialization state | not initialized / initializing / initialized / failed |

Identity is the canonical path, not the import specifier string.

Two imports that resolve to the same canonical path are one module.
v0.3 has a single specifier form, so this is demonstrated when two
modules import the same sibling name.

Initialization state exists so a module is never exposed to an importer
while still initializing, and is never treated as initialized after
failure.

---

## 4. ModuleResolver

**Input:** importer canonical path + bare module name.

**Output:** canonical absolute path of the dependency, or a resolver error.

Given importer `/project/app.echo` and name `math`, the resolver yields
`/project/math.echo`.

The `.echo` extension is implied and is not written in the specifier.

The resolver looks only beside the importing file.

The resolver:

* canonicalizes the resulting path;
* reports module-not-found when the sibling file is absent;
* does **not** parse, analyze, or execute modules;
* does **not** interpret `use`;
* does **not** accept `"math.echo"`, `"./math"`, `"../math"`, or subdirectory specifiers.

The resolver answers only: *which file is this import?*

---

## 5. ModuleGraph

**Input:** entry module path, plus the resolver.

**Output:** a graph of canonical paths, or a cycle error.

The graph:

* records directed dependencies from importer to imported file;
* deduplicates nodes by canonical path;
* detects direct, indirect, and longer cycles before any module is exposed;
* produces a dependency-first initialization order;
* places the entry module last among the modules it depends on.

The graph does **not** execute modules and does **not** bind names.

A cycle is a graph error. The error identifies the dependency problem.
No node in a rejected cycle is marked initialized.

---

## 6. ModuleLoader

**Input:** the module graph and an initialization order.

**Output:** initialized module records, or a load/initialization error.

The loader:

* loads and parses each module at most once per process;
* initializes dependencies before importers;
* executes each module’s top-level code exactly once;
* records exports after successful initialization;
* shares that initialized module state with every importer;
* marks the module failed if initialization fails;
* never exposes a partially initialized module.

The loader owns once-per-process initialization.
The interpreter executes a module body only when the loader asks it to.

A second import of an already-initialized module reuses the same record.
It does not parse or execute the file again.

---

## 7. Semantic Analyzer Integration

The analyzer validates module *names*. It does not walk the filesystem
and it does not execute module bodies.

After the graph exists, the analyzer:

* records which names a module exports;
* checks that each imported name is exported by the resolved dependency;
* rejects unknown exports and private names;
* rejects imported names that collide with an existing module-level binding;
* rejects importing the same name into the same module more than once;
* does not introduce non-selected exports into the importer;
* does not create a module namespace such as `math.add`;
* leaves `use` / `use mut` on their existing same-module rules.

Imported bindings are module-scope names. They are not mutable bindings
in the importing module. `use mut` on an imported name is a semantic error.

Function-local shadowing of an imported name remains ordinary lexical
shadowing. It does not write through to the imported binding.

The analyzer may require resolved module identities from the graph.
It must not call the resolver to execute or initialize anything.

Invalid import form (`import from "math"`) is a parse or semantic error,
not a resolver error.

---

## 8. Interpreter Integration

The interpreter receives already-resolved, already-ordered module
information from the loader.

It does not choose files, detect cycles, or decide initialization order.

When asked to initialize a module, the interpreter:

* creates an independent module scope for that file;
* binds selected imported names into that scope;
* those bindings refer to the exporting module’s values, not copies of collections;
* executes the module body under existing Echo rules;
* preserves definition-site lexical scope for functions;
* keeps importer locals invisible to imported functions;
* keeps `use` / `use mut` as same-module capture and mutability.

Imported bindings cannot be rebound.
Mutating an imported list or hash mutates the shared collection.

A program with no `import` keeps the current single-file pipeline:
analyze, then execute. No module graph is required.

---

## 9. Error Ownership

All module failures are Echo errors. Python exceptions must not leak.

| Category | Owner | Examples |
|---|---|---|
| resolver errors | ModuleResolver | sibling `.echo` file not found |
| graph / cycle errors | ModuleGraph | direct, indirect, or longer circular dependency |
| export / import semantic errors | Semantic Analyzer | name not exported, private import, binding collision, `use mut` across a module boundary, invalid import form |
| initialization / runtime errors | ModuleLoader + Interpreter | dependency top-level failure, ordinary runtime errors during module execution |

Wording is unspecified. Categories must remain distinguishable.
Tests require the category and relevant names, not a particular phrase.

A cycle error belongs to the graph, not the interpreter.
A missing export belongs to the analyzer, not the resolver.
A missing file belongs to the resolver, not the analyzer.

If initialization fails, the loader marks the module failed. Importers
do not receive its exports.

---

## 10. Component Boundaries

```text
import AST
    ↓
ModuleResolver          importer path + bare name
    ↓
canonical absolute path
    ↓
ModuleGraph             dedup, cycles, order
    ↓
Semantic Analyzer       exports, imports, collisions
    ↓
ModuleLoader            once-per-process init
    ↓
Interpreter             module scopes and bindings
```

Allowed crossings:

* the graph asks the resolver for paths;
* the analyzer reads graph identities and export sets;
* the loader asks the interpreter to execute one module body;
* the interpreter reads initialized exports from loader records.

Forbidden crossings:

* the parser resolving or loading files;
* the resolver executing or analyzing modules;
* the graph binding names or running top-level code;
* the analyzer performing filesystem execution;
* the interpreter choosing dependency order or detecting cycles;
* `use` entering the resolver, graph, or loader.

---

## 11. Explicit Non-Goals

These are outside the v0.3 architecture:

* import aliases (`import add as plus from "math"`);
* module namespaces (`math.add()`);
* packages or package-resolution semantics;
* standard-library module paths;
* dynamic / runtime imports;
* alternate specifiers (`"math.echo"`, `"./math"`, `"../math"`, `"lib/math"`);
* extra filesystem names or symbolic links as another way to spell a module;
* circular-import recovery or partial initialization;
* wildcard imports;
* re-exporting.

No component may grow a hook for these features in order to make an
import “more convenient.”

---

## 12. Test Coverage by Boundary

Every `tests/modules/` contract test must be explainable by a boundary
above. None of these tests require a new language rule.

### Identity — ModuleResolver + ModuleGraph

* every `.echo` file is a module
* CLI file is the entry module
* `.echo` extension is implied
* relative imports resolve beside the importer
* missing sibling is not found in another directory
* resolved absolute path defines module identity
* equivalent sibling imports resolve to one module identity

### Exports and selective imports — Semantic Analyzer + Interpreter

* names are private by default
* `export` makes a name visible
* private functions and variables cannot be imported
* multiple exports from one module work
* selective import binds only the selected export
* non-selected exports are not introduced
* unknown export fails
* imported names appear in importer module scope
* no namespace access exists

### `use` compatibility — existing analyzer / interpreter only

* `use` and `use mut` retain v0.2.1 behavior
* `use` does not load modules
* programs without `import` remain unchanged
* same-module `use mut` still works without imports

### Scope — Interpreter module scopes

* private names are inaccessible to importers
* importer locals are invisible to imported functions
* imported functions retain definition-site scope
* module boundaries prevent accidental name leakage
* imported name shadowing inside a function is ordinary lexical shadowing
* private module state captured by an exported function stays private

### Mutability — Interpreter bindings vs collection identity

* imported bindings cannot be rebound
* `use mut` cannot cross a module boundary
* imported lists and hashes share collection identity
* mutating an imported collection is visible to other references
* rebinding an imported collection is rejected
* imported mutable collections plus function mutation
* multiple importers sharing one mutable export

### Execution — ModuleLoader + Interpreter

* dependencies execute before importers
* entry module executes last
* a module executes once per process
* shared dependencies execute once
* module state is shared across importers
* top-level code executes exactly once
* shared dependency imported through two branches
* nested dependency plus closure
* module initialization failure does not run the importer

### Cycles — ModuleGraph

* direct, indirect, and longer cycles are rejected
* no partially initialized module is exposed
* cycle error identifies the dependency problem

### Errors — error ownership table

* missing module → resolver
* missing export → analyzer
* invalid import → parser / analyzer
* import collision, including after a local declaration → analyzer
* circular dependency → graph
* Python exceptions do not leak from any module component

### Interactions — existing language rules on top of the boundaries

Imported function plus closure, nested function, `use`, or `use mut`
does not change module loading. Those tests succeed only if the loader
initialized the defining module once and the interpreter kept
definition-site scope.

---

## 13. Implementation Boundary

This document names conceptual components, not source files.

The next design step is the resolver’s input/output contract.
That step still must not implement the resolver.

Implementation exists to satisfy `module-semantics.md`.
The architecture exists to keep that implementation from crossing
boundaries the contract never granted.
