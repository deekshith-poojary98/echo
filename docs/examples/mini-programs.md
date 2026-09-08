# Mini Programs

## Overview
A few short programs that show Echo as a practical scripting language.

## Syntax
```echo
fn countdown(start: int) {
    for i: int in start..0 by -1 {
        say(i);
    }
}
```

## Example
### Countdown
```echo
fn countdown(start: int) {
    for i: int in start..0 by -1 {
        say(i);
    }
}

countdown(3);
```

Output:
```text
3
2
1
0
```

### Simple frequency counter
```echo
words: list = ["a", "b", "a"];
counts: hash = {};

i: int = 0;
while i < words.length() {
    word: str = words[i];
    counts[word] = counts.ensure(word, 0) + 1;
    i = i + 1;
}

say(counts);
```

Output:
```text
{"a": 2, "b": 1}
```

### JSON job report (v0.4 host builtins)

`examples/json_report.echo` reads a JSON suite, prints a summary, and can write it back out.

```bash
echo examples/json_report.echo -- examples/sample_jobs.json
ECHO_REPORT=report.json echo examples/json_report.echo -- examples/sample_jobs.json
```

It uses `args()`, `envOr()`, `readFile()`, `writeFile()`, `parseJson()`, and `writeJson()`.

## Notes
These are still small scripts, but they cover the kind of tasks Echo currently handles well.

## See Also
- [Control Flow](/getting-started/control-flow)
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
