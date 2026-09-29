# Lesson 9 — Classes

**You are here**

1–8 done · **9. Classes** ←

## What are we learning?

A **class** is a blueprint for a kind of value that has:

- **fields** — named pieces of data
- **methods** — functions that belong to that kind of value

An **object** (or instance) is one value made from that blueprint.

## Smallest useful example

```echo
class Dog {
    new {
        name: str;
    }

    fn bark(this) {
        say(this.name, "says woof");
    }
}

d: Dog = Dog { name: "Rex" };
d.bark();
```

### Output

```text
Rex says woof
```

### Line by line

1. `class Dog { ... }` — define the blueprint named `Dog`.
2. `new { name: str; }` — every `Dog` has a text field called `name`.
3. `fn bark(this) { ... }` — a method. `this` means “the dog we are talking about.”
4. `Dog { name: "Rex" }` — create one dog whose name is Rex.
5. `d.bark();` — run `bark` on that dog.

## Try it

Create a `Cat` class with a `name` field and a `meow` method that prints the name and `says meow`. Make one cat and call `meow`.

## Predict it

```echo
class Point {
    new {
        x: int;
        y: int;
    }

    fn show(this) {
        say(this.x, this.y);
    }
}

p: Point = Point { x: 3, y: 4 };
p.show();
```

<details>
<summary>Show answer</summary>

```text
3 4
```

</details>

## What we are not covering yet

Interfaces, private fields (`priv`), getters/setters, type methods, and `implements` are real Echo features. Learn them after you are comfortable with this page: [Classes and Interfaces (full)](/examples/classes-and-interfaces).

## You finished the Learn path

Next steps:

1. [Practice — Change, predict, fix](/practice/change-predict-fix)
2. [Small exercises](/practice/small-exercises)
3. [Mini projects](/practice/mini-projects)
4. When you need exact rules: [Language Reference](/reference/language-reference)
5. When you already know other languages: [Language Tour](/getting-started/tour)
