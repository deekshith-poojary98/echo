# Common mistakes

This page is for **people learning Echo**. It explains problems in ordinary language.

Looking for error **codes** (E1001, E2003, …)? Use [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting).

For each problem:

```text
What you see → What it means → Why → How to fix → Try again
```

---

## Missing semicolon

### What you see

A message like: `Expected ;, got end of input` (or similar).

### What it means

Echo reached the end of an instruction and did not find `;`.

### Why it happened

You wrote something like:

```echo
say("Hello, Echo!")
```

### How to fix

Add `;` at the end:

```echo
say("Hello, Echo!");
```

### Try again

Run the fixed program. You should see `Hello, Echo!`.

---

## Variable used before it was declared

### What you see

Something like: `Variable 'count' is not declared` (often **E1011**), with a hint to declare with a type.

### What it means

You tried to assign to a name Echo has not been introduced to yet.

### Why it happened

```echo
count = 1;
```

### How to fix

Declare it the first time, with a type:

```echo
count: int = 1;
```

### Try again

```echo
count: int = 1;
say(count);
```

Should print `1`.

---

## Wrong type of value

### What you see

A type error when you assign or pass a value (message mentions types or **E** codes in the Type category).

### What it means

The name was declared for one kind of value (for example `int`), but you gave it another kind (for example text).

### Why it happened

```echo
count: int = 1;
count = "two";
```

### How to fix

Keep the same kind, or declare a different variable for text:

```echo
count: int = 1;
count = 2;
label: str = "two";
```

---

## `elang: command not found` {#elang-command-not-found}

### What you see

The Terminal says it does not know the command `elang`.

### What it means

Your computer is not finding the Echo install in this Terminal window.

### Why it happened

Common causes: install not finished, or you did not open a **new** Terminal after `pipx ensurepath`.

### How to fix

1. Open a **new** Terminal window.
2. Run `elang --version` again.
3. If it still fails, re-run:

   ```bash
   python3 -m pipx ensurepath
   ```

   (Windows PowerShell: `python -m pipx ensurepath`), then open another new Terminal.

4. Check `pipx list` mentions `echolang`.

Still stuck? On macOS/Linux, developers sometimes need `~/.local/bin` on PATH — see the longer checklist in [Install Echo](/getting-started/installation).

### Try again

Success looks like:

```text
Echo 2.2.0
```

---

## File not found when running

### What you see

Echo (or the shell) says it cannot find `hello.echo` (or similar).

### What it means

Terminal is looking in a folder that does not contain your file.

### How to fix

1. Note where you saved the file (Desktop, Documents, …).
2. `cd` into that folder.
3. Confirm the file name ends with `.echo`.
4. Run `elang hello.echo` again.

---

## Missing `{ }` after `if` / `while`

### What you see

A syntax error near `if` or `while`.

### What it means

Echo expects braces around the block.

### How to fix

```echo
if true {
    say("yes");
}
```

---

## Changing an outer variable inside a function

### What you see

An error about assignment / **E2003**, often mentioning `use mut`.

### What it means

Inside a function you may **read** a name from outside. To **change** it, Echo requires `use mut` first.

### How to fix (when you need it)

```echo
count: int = 0;

fn bump() {
    use mut count;
    count = count + 1;
}

bump();
say(count);
```

Beginners can avoid this pattern: pass values in as parameters and `return` new values instead. Full rules: [Scope, use, and watch](/core-concepts/scope-use-watch).

---

## Next

- Back to [Learn Echo](/learn/first-program)
- Full catalog: [Errors and Troubleshooting](/errors-diagnostics/errors-and-troubleshooting)
