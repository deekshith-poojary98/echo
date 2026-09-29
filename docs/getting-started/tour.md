# Language Tour

::: info This page is for people who already program
If you have **never** written code before, start with [Choose your path](/start/choose-your-path) and [Lesson 1](/learn/first-program) instead. This tour assumes JavaScript, C, or Python familiarity.
:::

Echo is interpreted. You declare types on variables and parameters; the runtime checks them when values are bound. Blocks use braces. If you know JavaScript, C, or Python, the surface should look familiar — the failure rules and scope rules will not.

This page is a first-hour map for experienced programmers. For a minimal file → run walkthrough, use [Quick Start](/getting-started/quick-start). For a teaching path, use [Learn Echo](/learn/first-program).

```echo
name: str = "Echo";
version: int = 1;

fn greet(user: str) {
    say("Hello, ${user}!");
}

greet(name);
say("Version:", version);
```

## Facts that matter early

- Not compiled. Files go lexer → parser → analyzer → interpreter.
- Declarations and parameters need types. A `return` requires a return type annotation on the function.
- Abort is the default on failure; inquiry and `*Or` twins cover expected absence — see [Failure model](/failure-model).
- Classes and interfaces ship: `new { ... }` fields, methods, type methods, unbound methods, optional `implements`. Class inheritance does not.
- Scripting helpers: HTTP (host-gated), URL / Base64, regex, UTC dates. List prelude names with `elang builtins`.
- Current package version: **2.1.9** (see [Known Limitations](/errors-diagnostics/known-limitations) for the feature timeline).
- Comments:

```echo
// single-line

/*
multi-line
*/
```

## Common mistakes

Missing `;`:

```echo
name: str = "Echo"
say(name);
```

Missing braces (Python-style bare body):

```echo
if true
    say("yes");
```

Use:

```echo
if true {
    say("yes");
}
```

## Where to go next

- [Syntax Basics](/getting-started/syntax-basics)
- [Variables and Types](/getting-started/variables-and-types)
- [Control Flow](/getting-started/control-flow)
- [Functions](/getting-started/functions)
- [Modules](/getting-started/modules)
- [Known Limitations](/errors-diagnostics/known-limitations)
