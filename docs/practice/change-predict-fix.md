# Practice — Change, predict, fix

Use these after [Lesson 1](/learn/first-program)–[Lesson 3](/learn/making-decisions). Run each program in the [Playground](/playground) or with `elang`.

This page is **practice**, not reference.

## Change it

### 1. Greeting

```echo
say("Hello, Echo!");
```

**Task:** Change the message to greet a friend.

### 2. Variable

```echo
name: str = "Echo";
say(name);
```

**Task:** Change the value so the program prints your name.

### 3. Decision

```echo
temp: int = 20;

if temp >= 25 {
    say("Warm");
} else {
    say("Cool");
}
```

**Task:** Change `temp` so the program prints `Warm`.

---

## Predict it

Do **not** run these until you write your guess.

### 4.

```echo
n: int = 2;
say(n + 3);
```

<details>
<summary>Answer</summary>

```text
5
```

</details>

### 5.

```echo
flag: bool = false;

if flag {
    say("yes");
} else {
    say("no");
}
```

<details>
<summary>Answer</summary>

```text
no
```

</details>

### 6.

```echo
i: int = 1;

while i <= 2 {
    say(i);
    i = i + 1;
}
```

<details>
<summary>Answer</summary>

```text
1
2
```

</details>

---

## Fix it

### 7. Missing semicolon

```echo
say("Hello, Echo!")
```

**Task:** Make it run. Hint: instructions end with `;`.

<details>
<summary>Fixed</summary>

```echo
say("Hello, Echo!");
```

</details>

### 8. Missing type on first use

```echo
count = 1;
say(count);
```

**Task:** Declare `count` properly.

<details>
<summary>Fixed</summary>

```echo
count: int = 1;
say(count);
```

</details>

### 9. Missing braces

```echo
if true
    say("ok");
```

<details>
<summary>Fixed</summary>

```echo
if true {
    say("ok");
}
```

</details>

---

## Next

→ [Small exercises](/practice/small-exercises)
