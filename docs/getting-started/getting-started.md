# Getting Started

## Overview
Echo is an interpreted scripting language with explicit variable types, brace-based blocks, and practical built-in methods.

If you know JavaScript, C, or Python, the surface syntax should feel familiar quickly.

## Syntax
```echo
name: str = "Echo";
version: int = 1;

fn greet(user: str) {
    say("Hello, ${user}!");
}

greet(name);
say("Version:", version);
```

## Example
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

## Output
```text
Echo
Echo
Echo
Total: 3
```

## Notes
- Echo is interpreted, not compiled.
- Variable declarations require a type.
- Function parameter types are required.
- Function return type annotations are optional.
- Comments:

```echo
// single-line

/*
multi-line
*/
```

## Common Mistakes
### Forgetting `;`
```echo
name: str = "Echo"
say(name);
```

### Forgetting braces
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
