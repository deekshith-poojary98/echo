# Neura

Neura is a modern, statically-typed programming language designed for simplicity and readability. It combines strong type safety with a clean, intuitive syntax and powerful features for modern programming needs.

## Features

- **Strong Type System**
  - Explicit type declarations
  - Type validation at runtime
  - Support for basic types: `int`, `float`, `str`, `bool`, `list`, `hash`
  - Dynamic type with `dynamic` keyword
  - Required type annotations for function parameters

- **Modern Syntax**
  - Clean and readable syntax
  - String interpolation with `${variable}` syntax
  - Method chaining support
  - Both inline (`=>`) and block-style function definitions
  - Type-safe function parameters

- **Control Structures**
  - `for` loops with step control
  - `foreach` loops for iteration
  - `while` loops
  - `if/else` conditionals
  - `break` and `continue` statements

- **Built-in Methods**
  - I/O: `say()`, `ask()`, `wait()`
  - Type Conversion: `asInt()`, `asFloat()`, `asBool()`, `asString()`
  - String Manipulation: `trim()`, `upperCase()`, `lowerCase()`, `length()`

- **Advanced Features**
  - Function closures
  - Context-based scoping
  - Method chaining

## Getting Started

### Installation

[Installation instructions to be added]

### Basic Syntax Examples

```c
// Variable Declaration with Types
x: int = 10;
name: str = "John";
scores: list = [95, 85, 75];
config: hash = {"debug": true, "port": 8080};

// String Interpolation
say("Hello, ${name}! Your score is ${scores[0]}");

// Function Definition (Block Style) with Type Annotations
fn greet(name: str) {
    say("Hello,", name);
}

// Function Definition (Inline) with Type Annotations
fn square(x: int) => x * x;

// Method Chaining
result: str = ask("Enter a number:").asInt().toString().length();

// Loops
for i in 0..10 by 2 {
    say("Count:", i);
}

foreach item in items {
    say("Processing:", item);
}

// Conditional
if score >= 90 {
    say("Excellent!");
} else {
    say("Good job!");
}
```

## Project Structure

- `src/` - Core language implementation
  - `neura_lexer.py` - Token generation
  - `neura_parser.py` - Abstract Syntax Tree (AST) construction
  - `neura_interpreter.py` - Code execution
- `neura-syntax-highlighter/` - Syntax highlighting support
- `source.neu` - Example Neura source file
- `index.html` - Web documentation

## Documentation

For more detailed documentation, please refer to:
- `neura_documentation.md` - Basic language documentation

## Contributing

[Contribution guidelines to be added]

## License

[License information to be added]
