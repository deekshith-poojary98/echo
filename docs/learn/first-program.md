# Lesson 1 — Your first program

**You are here**

1. **Your first program** ←
2. Values and variables
3. Making decisions
4. Repeating things
5. Functions
6. Lists and hashes
7. Strings
8. Organizing programs
9. Classes

## What are we learning?

You will write one instruction, run it, and see text appear.

A **program** is a list of instructions for the computer.

An **instruction** is one step, like “print this sentence.”

## The smallest useful program

```echo
say("Hello, Echo!");
```

### What each part means

| Piece | Meaning |
| --- | --- |
| `say` | Tell Echo to print something |
| `( ... )` | The thing to print goes inside |
| `"Hello, Echo!"` | Text (words) — always in quotes |
| `;` | End of this instruction |

### Output

```text
Hello, Echo!
```

## How to run it

### In the Playground

1. Open the [Playground](/playground).
2. Wait until status shows **Ready**.
3. Make sure the left side contains the line above (or choose the **Hello** example).
4. Click **Run**.
5. Read the **OUTPUT** panel on the right.

### On your computer

1. Save the line in a file named `hello.echo`.
2. In Terminal, go to that folder.
3. Run:

```bash
elang hello.echo
```

(See [Install Echo](/getting-started/installation) if `elang` is not set up yet.)

## Try it — change the message

Change the text inside the quotes to your name, for example:

```echo
say("Hello, Ada!");
```

Expected output:

```text
Hello, Ada!
```

Run it again. You just changed an Echo program.

## Fix it — missing semicolon

This is **wrong** (no `;` at the end):

```echo
say("Hello, Echo!")
```

Echo stops and says it expected `;`.

Add the semicolon and run again.

## What you learned

- A program is a list of instructions.
- `say` prints text.
- Text goes in quotes.
- Instructions end with `;`.

## Next

→ [Lesson 2 — Values and variables](/learn/values-and-variables)

Also: [Choose your path](/start/choose-your-path) · [Common mistakes](/errors-diagnostics/common-mistakes)
