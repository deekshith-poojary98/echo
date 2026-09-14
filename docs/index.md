---
layout: home

title: Echo
titleTemplate: Official Documentation
hero:
  name: Echo
  text: A small interpreted scripting language
  tagline: Explicit types checked at runtime. Brace blocks. Abort on failure unless you use inquiry or *Or twins.
  actions:
    - theme: brand
      text: Start Here
      link: /getting-started/quick-start
    - theme: alt
      text: Playground
      link: /playground
    - theme: alt
      text: Language Reference
      link: /reference/language-reference
features:
  - title: Typed declarations
    details: Variables and parameters carry types. Echo checks them when values are bound, not with a separate static checker.
  - title: Scripting surface
    details: Strings, lists, hashes, loops, functions, modules, and a stdlib for I/O and collections.
  - title: Documented limits
    details: Held items (classes, try/catch, generics) are listed up front. Do not assume a pattern is supported until you see it here.
---

## Quick Example

```echo
name: str = "Echo";

fn greet(user: str) {
    say("Hello, ${user}!");
}

greet(name);
```

Output:

```text
Hello, Echo!
```

## Start Here

- [Installation](/getting-started/installation)
- [Quick Start](/getting-started/quick-start)
- [Getting Started](/getting-started/getting-started)
- [Variables and Types](/getting-started/variables-and-types)
- [Strings and Interpolation](/getting-started/strings-and-interpolation)
- [Control Flow](/getting-started/control-flow)
- [Functions](/getting-started/functions)

## What ships today

- Typed declarations and runtime type checks (`int`, `float`, `str`, `bool`, `list`, `hash`, `dynamic`, unions, aliases)
- Control flow: `if`, `while`, `for`, `foreach`, `break`, `continue`
- Named functions, lambdas, keyword args, `use mut`, file modules (`import` / `export`)
- CLI: run, REPL, `check`, `test`, `fmt`, `lint`
- Failure model: abort by default; inquiry and `*Or` twins for expected absence — see [Failure model](/failure-model)

## What does not

- No classes or user-defined structs
- No generics
- No `try` / `catch` (held)
- Outer reassignment from a function still needs `use mut`

Read [Known Limitations](/errors-diagnostics/known-limitations) before treating a pattern as guaranteed.

## Reference

- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Loops Reference](/reference/loops-reference)
- [CLI and Execution Model](/reference/cli-and-execution-model)
- [Language Reference](/reference/language-reference)
