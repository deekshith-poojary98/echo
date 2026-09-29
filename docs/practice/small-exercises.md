# Small exercises

Build short programs using only ideas from the Learn lessons. Hints are below each task; solutions are collapsed.

## Exercise A — Two lines

Print your name, then print the number `1`.

<details>
<summary>Hint</summary>

Use two `say` instructions. Numbers do not need quotes. Text does.

</details>

<details>
<summary>One solution</summary>

```echo
say("Ada");
say(1);
```

</details>

## Exercise B — Age check

Store an age in a variable. If it is at least `18`, print `Adult`. Otherwise print `Young`.

<details>
<summary>Hint</summary>

Lesson 3: `if` / `else`, type `int`.

</details>

<details>
<summary>One solution</summary>

```echo
age: int = 20;

if age >= 18 {
    say("Adult");
} else {
    say("Young");
}
```

</details>

## Exercise C — Countdown

Print `3`, then `2`, then `1` using a `while` loop.

<details>
<summary>Hint</summary>

Start at `3`. While the number is at least `1`, print it, then subtract `1`.

</details>

<details>
<summary>One solution</summary>

```echo
n: int = 3;

while n >= 1 {
    say(n);
    n = n - 1;
}
```

</details>

## Exercise D — Greeter function

Write a function `greet` that takes a `str` name and prints `Hello,` followed by that name. Call it with `"Echo"`.

<details>
<summary>Hint</summary>

Lesson 5: `fn greet(name: str) { ... }` then `greet("Echo");`.

</details>

<details>
<summary>One solution</summary>

```echo
fn greet(name: str) {
    say("Hello,", name);
}

greet("Echo");
```

</details>

## Exercise E — First list item

Create a list of three numbers. Print only the first item, then print the whole list after pushing `99`.

<details>
<summary>One solution</summary>

```echo
nums: list = [10, 20, 30];
say(nums[0]);
nums.push(99);
say(nums);
```

</details>

## Next

→ [Mini projects](/practice/mini-projects)
