---
layout: home

title: Echo
titleTemplate: Official Documentation
hero:
  name: Echo
  text: A small scripting language with explicit types and practical built-ins
  tagline: Clean syntax, runtime type checks, useful collection methods, and honest documentation.
  actions:
    - theme: brand
      text: Start Here
      link: /getting-started/quick-start
    - theme: alt
      text: Language Reference
      link: /reference/language-reference
features:
  - title: Explicit by default
    details: Variables and function parameters are typed, and Echo checks those types at runtime.
  - title: Small but practical
    details: Strings, lists, hashes, loops, functions, interpolation, and collection helpers cover real scripting tasks.
  - title: Honest about limits
    details: Missing features and incomplete behavior are documented clearly instead of being buried.
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

## What Echo Covers Today

- Explicit variable declarations with runtime type enforcement
- Strings, booleans, `null`, lists, and hashes
- `if`, `while`, `for`, `foreach`, `break`, and `continue`
- Named functions, inline functions, keyword arguments, and strict function scope
- Built-in methods for I/O, conversion, formatting, lists, and hashes

## Current Limitations

Echo is usable today, but it is not a complete general-purpose language yet.

- No module system for Echo source files
- No classes or user-defined structs
- No generics
- No exceptions such as `try/catch`
- Some behaviors are intentionally strict, especially function scope

Read [Known Limitations](/errors-diagnostics/known-limitations) before treating a pattern as guaranteed.

## Reference Entry Points

- [Built-in Methods](/standard-library/built-in-methods)
- [Operators](/reference/operators)
- [Loops Reference](/reference/loops-reference)
- [CLI and Execution Model](/reference/cli-and-execution-model)
- [Language Reference](/reference/language-reference)
