# Echo Programming Language

Echo is a modern, statically-typed programming language designed for simplicity and readability. It combines strong type safety with a clean, intuitive syntax and powerful features for modern programming. Checkout documentation [here](https://deekshith-poojary98.github.io/echo/index.html).

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
- `null` literal support
- Type conversion methods: `asInt()`, `asFloat()`, `asBool()`, `asString()`

### Type System Updates
- Type aliases are supported via `type Alias = BaseType;`
- Object type aliases are supported, e.g. `type User = { id: int, username: str, email: str, isAdmin: bool };`
- Function calls support keyword arguments, e.g. `greet(name: "Alice", age: 21);`
- Type inference is still limited (explicit declarations are required)
- Generic types are not yet supported

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

## Verified Examples

```c
// null literal
x: dynamic = null;
say(x);  // Output: None

// primitive alias
type Age = int;
age: Age = 5;
say(age);  // Output: 5

// object alias + typed function parameter
type User = { id: int, username: str, email: str, isAdmin: bool };

fn greet(user: User) -> void {
  say("Hello, ${user['username']}!");
}

user: User = {
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "isAdmin": false
};

greet(user);  // Output: Hello, alice!

// keyword arguments
fn describe(name: str, age: int) -> void {
  say(name, "is", age);
}

describe(age: 21, name: "Alice");  // Output: Alice is 21
```

## Project Structure

- `src/` - Core language implementation
  - `echo_lexer.py` - Token generation and lexical analysis
  - `echo_parser.py` - Abstract Syntax Tree (AST) construction
  - `echo_interpreter.py` - Code execution and runtime
  - `main.py` - Entry point for the interpreter
- `docs/` - VitePress documentation site (source + build config)
- `docs-legacy/` - Legacy static documentation files
- `*.echo` - Example source files

## Installation

Echo can be installed as a proper CLI command (`echo` / `echolang`) like other language runtimes.

### Prerequisites
- Python 3.10+

### Option 1: Global install with pipx (recommended)
`pipx` installs Echo in an isolated environment and exposes global commands.

1. Install `pipx` (if needed):

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

2. Install Echo from GitHub:

```powershell
pipx install git+https://github.com/deekshith-poojary98/echo.git
```

3. Run Echo:

```powershell
echolang examples\language_feature_smoke.echo
```

### Option 2: Install from source with pip
If you cloned this repo, install it as a package:

```bash
pip install .
```

Then run:

```bash
echo examples/language_feature_smoke.echo
```

On PowerShell, use `echolang` because `echo` is a built-in alias.

### Option 3: Developer editable install
For contributors who want live code updates without reinstall:

```bash
pip install -e .
```

### Commands
After installation, these commands are available:

```bash
echo path/to/file.echo
echolang path/to/file.echo
```

In Windows PowerShell, prefer `echolang path/to/file.echo`.

### Local development launcher (without install)
You can still run directly from the repository:

#### Windows

```powershell
.\echolang.bat examples\language_feature_smoke.echo
```

#### macOS / Linux

```bash
chmod +x echolang
./echolang examples/language_feature_smoke.echo
```

### Direct Python entrypoint (all platforms)
You can also run Echo directly with Python:

```bash
python src/main.py examples/language_feature_smoke.echo
```

Use plain error output (no Rich formatting):

```bash
python src/main.py examples/language_feature_smoke.echo --plain
```

## Getting Started

1. Clone the repository
2. Check out the [documentation](https://deekshith-poojary98.github.io/echo/index.html)
3. Try the example files in the repository

## Contributing

[Contribution guidelines to be added]

## License

[License information to be added]
