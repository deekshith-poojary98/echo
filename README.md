# Echo Programming Language

Echo is a modern, statically-typed programming language designed for simplicity and readability. It combines strong type safety with a clean, intuitive syntax and powerful features for modern programming. Checkout documentation [here](https://deekshith-poojary98.github.io/echo/).

## Quick Overview

Echo is designed to be both beginner-friendly and powerful, offering:

- **Type Safety**: Strong static typing with mandatory type annotations and runtime type checking
- **Modern Syntax**: Clean, readable code with intuitive constructs and method chaining
- **Rich Standard Library**: Comprehensive built-in methods for common operations
- **Advanced Features**: Support for modern programming patterns and debugging tools

## Key Features

### Core Language Features
- Static typing with mandatory type annotations
- String interpolation with `${variable}` syntax
- Method chaining for fluent code
- Function closures and nested functions
- Context-based scoping with `use` and `use mut` statements
- Variable watching for debugging

### Data Types
- Basic types: `int` (32-bit), `float` (64-bit), `str` (UTF-8), `bool`
- Collections: `list` (mutable arrays), `hash` (key-value pairs)
- Dynamic typing with `dynamic` keyword
- Type conversion methods: `asInt()`, `asFloat()`, `asBool()`, `asString()`

### Control Flow
- `for` loops with step control (`by` keyword)
- `foreach` loops for collection iteration
- `while` loops
- `if/else` conditionals
- `break` and `continue` statements
- Logical operators: `&&`, `||`, `!`

### Built-in Methods
- I/O: `say()`, `ask()`, `wait()`
- String manipulation: `trim()`, `upperCase()`, `lowerCase()`, `length()`, `reverse()`
- Collection operations: `push()`, `empty()`, `clone()`, `countOf()`, `find()`, `insertAt()`, `pull()`, `removeValue()`, `order()`, `merge()`
- Type checking: `type()`

### Collection Methods
- List operations: `push()`, `empty()`, `clone()`, `countOf()`, `find()`, `insertAt()`, `pull()`, `removeValue()`, `order()`, `merge()`
- Hash operations: `keys()`, `values()`, `wipe()`, `clone()`, `pairs()`, `take()`, `take_last()`, `ensure()`, `merge()`

## Quick Example

```c
// Basic syntax example
name: str = "Echo";
age: int = 25;
scores: list = [95, 85, 75];

// Function with type annotations
fn greet(name: str) -> void {
    say("Hello, ${name}!");
}

// Method chaining
result: int = ask("Enter a number:").asInt().toString().length();

// Loop with step
for i: int in 0..10 by 2 {
    say("Count:", i);
}

// Variable watching
watch counter;
counter = counter + 1;  // Output: WATCH: counter changed to 1
```

## Project Structure

- `src/` - Core language implementation
  - `echo_lexer.py` - Token generation and lexical analysis
  - `echo_parser.py` - Abstract Syntax Tree (AST) construction
  - `echo_interpreter.py` - Code execution and runtime
  - `main.py` - Entry point for the interpreter
- `docs/` - Documentation and examples
- `*.echo` - Example source files

## Getting Started

1. Clone the repository
2. Check out the [documentation](https://deekshith-poojary98.github.io/echo/)
3. Try the example files in the repository

## Contributing

[Contribution guidelines to be added]

## License

[License information to be added]
