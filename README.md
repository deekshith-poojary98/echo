#  Echo Programming Language

Echo is a modern, statically-typed programming language designed for simplicity and readability. It combines strong type safety with a clean, intuitive syntax and powerful features for modern programming.

## Features

- **Strong Type System**
  - Explicit type declarations with mandatory type annotations
  - Type validation at runtime
  - Support for basic types: `int`, `float`, `str`, `bool`, `list`, `hash`
  - Dynamic type with `dynamic` keyword
  - Required type annotations for function parameters and return types

- **Modern Syntax**
  - Clean and readable syntax
  - String interpolation with `${variable}` syntax
  - Method chaining support
  - Both inline (`=>`) and block-style function definitions
  - Type-safe function parameters and return types
  - Logical operators with proper precedence (`&&`, `||`, `!`)

- **Control Structures**
  - `for` loops with step control (`by` keyword)
  - `foreach` loops for iteration
  - `while` loops
  - `if/else` conditionals
  - `break` and `continue` statements

- **Built-in Methods**
  - I/O: `say()`, `ask()`, `wait()`
  - Type Conversion: `asInt()`, `asFloat()`, `asBool()`, `asString()`
  - String Manipulation: `trim()`, `upperCase()`, `lowerCase()`, `length()`
  - Type Checking: `type()`

- **Advanced Features**
  - Function closures
  - Context-based scoping
  - Method chaining
  - Short-circuit evaluation for logical operators

## Project Structure

- `src/` - Core language implementation
  - `echo_lexer.py` - Token generation and lexical analysis
  - `echo_parser.py` - Abstract Syntax Tree (AST) construction
  - `echo_interpreter.py` - Code execution and runtime
  - `main.py` - Entry point for the interpreter
- `echo-syntax-highlighter/` - Syntax highlighting support
- `*.echo` - Example Echo source files
  - `source.echo` - Main example file
  - `test.echo` - Test cases
  - `mut.echo` - Mutation testing examples
- `index.html` - Web interface and documentation
- `echo_documentation.md` - Comprehensive language documentation
- `Echo Design Plan.docx` - Detailed design specifications

## Documentation

The project includes extensive documentation:

- `echo_documentation.md` - Complete language reference and guide
- `Echo Design Plan.docx` - Detailed design specifications
- `index.html` - Web-based documentation and examples

## Getting Started

### Basic Syntax Examples

```echo
// Variable Declaration with Types
x: int = 10;
name: str = "John";
scores: list = [95, 85, 75];
config: hash = {"debug": true, "port": 8080};

// String Interpolation
say("Hello, ${name}! Your score is ${scores[0]}");

// Function Definition with Return Type
fn greet(name: str) -> void {
    say("Hello,", name);
}

// Function Definition (Inline) with Return Type
fn square(x: int) -> int => x * x;

// Method Chaining
result = ask("Enter a number:").asInt().toString().length();

// Loops with Step Control
for i in 0..10 by 2 {
    say("Count:", i);
}

// Logical Operations
if age >= 18 && has_id && !is_banned {
    say("Access granted");
}
```

## Contributing

[Contribution guidelines to be added]

## License

[License information to be added]
