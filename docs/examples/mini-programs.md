# Mini Programs

Short scripts. Not a tutorial series.

### Countdown

```echo
fn countdown(start: int) {
    for i: int in start..0 by -1 {
        say(i);
    }
}

countdown(3);
```

```text
3
2
1
0
```

### Frequency counter

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

```text
{"a": 2, "b": 1}
```

### JSON job report

`examples/json_report.echo` reads a JSON suite, prints a summary, and can write it back out.

```bash
echolang examples/json_report.echo -- examples/sample_jobs.json
ECHO_REPORT=report.json echolang examples/json_report.echo -- examples/sample_jobs.json
```

Uses `args()`, `envOr()`, `readFile()`, `writeFile()`, `parseJson()`, and `writeJson()`.

## See Also

- [Control Flow](/getting-started/control-flow)
- [Lists](/core-concepts/lists)
- [Hashes](/core-concepts/hashes)
