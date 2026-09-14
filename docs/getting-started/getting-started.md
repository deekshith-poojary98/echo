# Getting Started

Echo is interpreted. You declare types on variables and parameters; the runtime checks them when values are bound. Blocks use braces. If you know JavaScript, C, or Python, the surface should look familiar — the failure rules and scope rules will not.

```echo
name: str = "Echo";
version: int = 1;

fn greet(user: str) {
    say("Hello, ${user}!");
}

greet(name);
say("Version:", version);
```

```echo
project: str = "Echo";
count: int = 3;

fn repeat_title(title: str) {
    say(title);
    say(title);
    say(title);
}

repeat_title(project);
say("Total:", count);
```

```text
Echo
Echo
Echo
Total: 3
```

## Facts that matter early

- Not compiled. Files go lexer → parser → analyzer → interpreter.
- Declarations and parameters need types. A `return` requires a return type annotation on the function.
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

## See Also

- [Syntax Basics](/getting-started/syntax-basics)
- [Control Flow](/getting-started/control-flow)
- [Functions](/getting-started/functions)
- [Known Limitations](/errors-diagnostics/known-limitations)
