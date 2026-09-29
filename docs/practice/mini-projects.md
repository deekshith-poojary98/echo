# Mini projects

Small programs that use ideas from the Learn path. Do not jump ahead to advanced features just to finish these.

Run with the [Playground](/playground) or `elang yourfile.echo`.

---

## Project 1 — Personalized greeting (Playground-friendly)

**Goal:** Ask for a name, then greet that person.

You will need `ask` (reads one line of typed text) from Lesson 1 skills plus Lesson 2 variables.

```echo
name: str = ask("What is your name? ");
say("Hello,", name);
```

**Try:** Run it, type a name, press Enter.

**Expected shape** (when you type interactively):

```text
What is your name? Ada
Hello, Ada
```

(If input is piped in without echoing, the greeting may appear on the same line as the prompt. That is normal for non-interactive runs.)

**Stretch:** Greet using interpolation: `say("Hello, ${name}!");`

---

## Project 2 — Number quiz

**Goal:** Store a secret number. Ask the player for a guess (`ask` returns text). Convert with `asInt` and say whether the guess is too low, too high, or correct.

Hints:

- `guess_text: str = ask("Guess: ");`
- `guess: int = asInt(guess_text);`
- Use `if` / `else if` / `else` from Lesson 3.

<details>
<summary>One solution</summary>

```echo
secret: int = 7;
guess_text: str = ask("Guess: ");
guess: int = asInt(guess_text);

if guess < secret {
    say("Too low");
} else if guess > secret {
    say("Too high");
} else {
    say("Correct");
}
```

</details>

::: tip
`asInt` stops with an error if the text is not a whole number. That is OK for this project. Safer variants like `asIntOr` are covered later in reference material.
:::

---

## Project 3 — Shopping list

**Goal:** Make a `list` of three items (text). Print each item with a `while` loop and `length()`, then push a fourth item and print the list.

<details>
<summary>One solution</summary>

```echo
items: list = ["milk", "eggs", "bread"];
i: int = 0;

while i < items.length() {
    say(items[i]);
    i = i + 1;
}

items.push("butter");
say(items);
```

</details>

---

## Project 4 — Two-file adder (local install)

**Goal:** Split a tiny program across two files like Lesson 8.

1. `math.echo` exports `add`.
2. `app.echo` imports it and prints `add(6, 7)`.
3. Run `elang app.echo` from that folder.

Expected output:

```text
13
```

This project needs the installed CLI (not the single-file playground).

---

## After the projects

- Review [Common mistakes](/errors-diagnostics/common-mistakes)
- Browse [Language Reference](/reference/language-reference) when you need exact rules
- Explore [Advanced](/getting-started/tour) when you are ready
