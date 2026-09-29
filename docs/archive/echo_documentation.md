# Echo Language Documentation

## Table of Contents
1. [Language Overview](#language-overview)
2. [Data Types](#data-types)
3. [Core Features](#core-features)
   - [Variable Declarations and Type Annotations](#1-variable-declarations-and-type-annotations)
   - [Functions](#2-functions)
   - [Control Structures](#3-control-structures)
   - [Logical Operators](#4-logical-operators)
   - [Collection Methods](#5-collection-methods)
   - [String Interpolation](#6-string-interpolation)
   - [Method Chaining](#7-method-chaining)
   - [Variable Watching](#8-variable-watching)
4. [Built-in Methods](#built-in-methods)
5. [Advanced Features](#advanced-features)
6. [Best Practices and Edge Cases](#best-practices-and-edge-cases)
7. [Syntax Requirements](#syntax-requirements)
8. [Variable Scoping and Mutability](#variable-scoping-and-mutability)
9. [Known Issues and Limitations](#known-issues-and-limitations)
10. [Future Improvements](#future-improvements)

## Language Overview

Echo is a statically-typed programming language with dynamic capabilities. It supports various data types, control structures, and methods for data manipulation. The language emphasizes type safety while providing flexibility through dynamic typing when needed.

## Data Types

- **int**: Integer values (32-bit)
- **float**: Floating-point values
- **str**: String values
- **bool**: Boolean values (true/false)
- **list**: Array-like collections
- **hash**: Dictionary-like key-value pairs
- **dynamic**: Variables that can change type

## Core Features

### 1. Variable Declarations and Type Annotations

```c
// Basic type declarations
age: int = 25;
name: str = "John";
is_active: bool = true;
numbers: list = [1, 2, 3];
config: hash = {"debug": true, "port": 8080};
dynamic_var: dynamic = 42;

// Type checking
say("Type of x:", x.type());
say("Type of y:", y.type());
say("Type of name:", name.type());
```

### 2. Functions

```c
// Standard function with block body and return type
fn process_data(age: int, is_active: bool) -> int {
    if is_active {
        return age * 1.5;
    }
    return age;
}

// Inline function with arrow syntax and return type
fn add(a: int, b: int) -> int => a + b;

// Function with void return type
fn greet(name: str) -> void {
    say("Hello, ", name);
}

// Function with dynamic return type (use sparingly)
fn get_value(key: str) -> dynamic {
    if key == "age" {
        return 25;  // Returns int
    }
    return "unknown";  // Returns string
}
```

#### Function Return Types
Every function must specify a return type using the `->` operator. Echo supports the following return types:
- `void` - For functions that don't return a value
- `int` - For functions returning integer values
- `float` - For functions returning floating-point numbers
- `str` - For functions returning strings
- `bool` - For functions returning boolean values
- `list` - For functions returning lists
- `hash` - For functions returning hash maps
- `dynamic` - For functions that may return different types (use sparingly)

#### Type Safety in Functions
- Return type annotations are mandatory
- The actual return value must match the declared return type
- Type mismatches will raise a TypeError
- Void functions cannot return any value
- Dynamic return types should be used sparingly and only when necessary

#### Common Type Errors
```c
// Error: Function declares int return type but returns float
fn calculate_average(a: int, b: int) -> int {
    return (a + b) / 2.0;  // TypeError: Expected int, got float
}

// Error: Function declares void return type but returns a value
fn print_message(msg: str) -> void {
    say(msg);
    return "done";  // TypeError: void function cannot return a value
}

// Error: Missing return type annotation
fn add_numbers(a: int, b: int) {  // SyntaxError: Return type annotation required
    return a + b;
}
```

### 3. Control Structures

#### If-Else Statements

```c
if condition {
    // code
} else if another_condition {
    // code
} else {
    // code
}
```

#### Loops

```c
// For loop with step
for i: int in 0..10 by 2 {
    say("Count:", i);
}

// Foreach loop
item: list = ["apple", "banana", "manago"];
foreach item: str in items {
    say("Processing:", item);
}

// While loop
while x > 0 {
    x = x - 1;
    say("x is now:", x);
}
```

### 4. Logical Operators

Echo supports three logical operators for boolean operations:

#### Logical AND (&&)
- Returns `true` if both operands are `true`
- Returns `false` if either operand is `false`
- Short-circuits: if the first operand is `false`, the second operand is not evaluated

```c
// Basic AND operation
is_valid: bool = true;
has_permission: bool = true;
if is_valid && has_permission {
    say("Access granted");
}

// Short-circuit example
if false && some_expensive_operation() {
    // some_expensive_operation() will never be called
    say("This will never execute");
}
```

#### Logical OR (||)
- Returns `true` if either operand is `true`
- Returns `false` if both operands are `false`
- Short-circuits: if the first operand is `true`, the second operand is not evaluated

```c
// Basic OR operation
is_admin: bool = false;
has_privileges: bool = true;
if is_admin || has_privileges {
    say("User has sufficient privileges");
}

// Short-circuit example
if true || some_expensive_operation() {
    // some_expensive_operation() will never be called
    say("This will execute immediately");
}
```

#### Logical NOT (!)
- Returns `true` if the operand is `false`
- Returns `false` if the operand is `true`
- Can be used to invert any boolean expression

```c
// Basic NOT operation
is_disabled: bool = false;
if !is_disabled {
    say("Feature is enabled");
}

// Complex NOT operation
if !(x > 5 && y < 10) {
    say("Either x is not greater than 5 or y is not less than 10");
}
```

#### Operator Precedence
1. `!` (highest precedence)
2. `&&`
3. `||` (lowest precedence)

```c
// Parentheses can be used to override precedence
if (x > 5 || y < 10) && !is_disabled {
    say("Complex condition met");
}
```

#### Type Safety
- Logical operators only work with boolean values
- Non-boolean values will raise a TypeError
- Use `asBool()` for type conversion when needed

```c
// Type-safe usage
value: int = 42;
if value.asBool() && is_valid {
    say("Value is truthy and valid");
}

// Error: Cannot use non-boolean with logical operators
if 42 && true {  // TypeError: Expected bool, got int
    say("This will cause an error");
}
```

#### Common Patterns
```c
// Checking multiple conditions
if age >= 18 && has_id && !is_banned {
    say("User is eligible");
}

// Providing default values
result = value || default_value;

// Toggling boolean state
is_enabled = !is_enabled;

// Complex conditions
if (!is_logged_in || !has_permission) && !is_guest {
    say("Access denied");
}
```

### 5. Collection Methods

```c
// Length method
str = "hello";
list = [1, 2, 3];
hash = {"a": 1, "b": 2};

say(str.length());  // 5
say(list.length()); // 3
say(hash.length()); // 2

// Keys and Values methods (for hashes only)
keys = hash.keys();   // ["a", "b"]
values = hash.values(); // [1, 2]

// List Methods
numbers: list = [1, 2, 3];
say(numbers.length());  // 3

// Adding elements
numbers.push(4);
say(numbers);  // [1, 2, 3, 4]

// Counting occurrences
numbers.push(2);
say(numbers.countOf(2));  // 2

// Finding elements
say(numbers.find(3));  // 2

// Inserting elements
numbers.insertAt(1, 10);
say(numbers);  // [1, 10, 2, 3, 4, 2]

// Removing elements
removed = numbers.pull(2);
say(removed);  // 2
say(numbers);  // [1, 10, 3, 4, 2]

// Removing values
numbers.removeValue(2);
say(numbers);  // [1, 10, 3, 4]

// Sorting
numbers.order();
say(numbers);  // [1, 3, 4, 10]

// Merging lists
other: list = [20, 30];
numbers.merge(other);
say(numbers);  // [1, 3, 4, 10, 20, 30]

// Cloning lists
copy = numbers.clone();
say(copy);  // [1, 3, 4, 10, 20, 30]

// Emptying lists
numbers.empty();
say(numbers);  // []

// String Methods
text: str = "  Hello World  ";
clean: str = text.trim();  // "Hello World"
upper: str = text.upperCase();  // "HELLO WORLD"
lower: str = text.lowerCase();  // "hello world"
reversed: str = text.reverse();  // "dlroW olleH"
```

## Hash Methods

Hash methods for manipulating key-value pairs:

### keys()
Returns list of hash keys

```c
user: hash = {"name": "Alice", "age": 25, "city": "New York"};
keys: list = user.keys();  // ["name", "age", "city"]
```

### values()
Returns list of hash values

```c
user: hash = {"name": "Alice", "age": 25, "city": "New York"};
values: list = user.values();  // ["Alice", 25, "New York"]
```

### wipe()
Removes all key-value pairs from the hash.

```c
d: hash = {"a": 1, "b": 2};
d.wipe();  // d is now {}
```

### clone()
Creates a shallow copy of the hash.

```c
d1: hash = {"x": 10};
d2: hash = d1.clone();  // d2 is {"x": 10}
```

### pairs()
Returns a list of [key, value] pairs.

```c
d: hash = {"a": 1, "b": 2};
items: dynamic = d.pairs();  // [["a", 1], ["b", 2]]
```

### take(key)
Removes and returns the [key, value] pair for the given key.

```c
d: hash = {"a": 100, "b": 200};
pair: list = d.take("a");  // pair is ["a", 100], d is {"b": 200}
```

### take_last()
Removes and returns the last [key, value] pair.

```c
d: hash = {"one": 1, "two": 2};
last: list = d.take_last();  // last is ["two", 2], d is {"one": 1}
```

### ensure(key, default)
Ensures a key exists with the given default value if not present.

```c
d: hash = {};
val: int = d.ensure("count", 0);  // val is 0, d is {"count": 0}
```

### merge(other)
Merges another hash into this one, overwriting existing keys.

```c
d1: hash = {"a": 1};
d2: hash = {"b": 2};
d1.merge(d2);  // d1 is {"a": 1, "b": 2}
```

## Best Practices

- Use `wipe()` to clear a hash completely
- Use `clone()` when you need a copy to avoid modifying the original
- Use `take()` when you need to remove and use a specific key-value pair
- Use `take_last()` when you need to remove and use the last key-value pair
- Use `ensure()` to safely get or set a default value for a key
- Use `merge()` to combine hashes, being aware that it overwrites existing keys

### 6. String Interpolation

```c
name = "John";
age = 25;
say("Hello, ${name}! You are ${age} years old.");
```

### 7. Method Chaining

```c
result = ask("Enter a number:").asInt().toString().length();
```

### 8. Variable Watching

The watch statement allows you to monitor variable changes during program execution. This is particularly useful for debugging and understanding program flow.

```c
// Watch a single variable
watch counter;

// Watch multiple variables
watch x, y, z;

// Example with variable watching
counter: int = 10;
watch counter;
counter = 20;  // Output: WATCH: counter changed to 20 (in global)
counter = 30;  // Output: WATCH: counter changed to 30 (in global)

// Watching in function scope
fn process_data() -> void {
    local_var: int = 5;
    watch local_var;
    local_var = 10;  // Output: WATCH: local_var changed to 10 (in process_data)
}

// Watching multiple variables in different scopes
global_var: int = 100;
watch global_var;

fn nested_function() -> void {
    local_var: int = 200;
    watch local_var, global_var;
    local_var = 300;   // Output: WATCH: local_var changed to 300 (in nested_function)
    global_var = 400;  // Output: WATCH: global_var changed to 400 (in nested_function)
}
```

#### Watch Features
- Monitor single or multiple variables in one statement
- Track changes in both global and local scopes
- Automatic unwatching when variables go out of scope
- Monitor modifications through assignments and method calls

#### Best Practices
1. Use watch statements strategically for debugging
2. Avoid watching too many variables simultaneously
3. Consider scope when watching variables
4. Use watch in combination with other debugging tools

#### Limitations
1. Cannot watch variables that don't exist
2. Cannot watch constants
3. Performance impact when watching many variables
4. No watch history beyond the current execution

## Built-in Methods

### I/O Methods
- `say(...)`: Prints values to the console
- `ask(prompt)`: Prompts user for input
- `wait(seconds)`: Pauses execution for specified duration

### Type Conversion Methods
- `asInt()`: Converts to integer
- `asFloat()`: Converts to float
- `asBool()`: Converts to boolean
- `asString()`: Converts to string

### String Methods
- `trim()`: Removes whitespace
- `upperCase()`: Converts to uppercase
- `lowerCase()`: Converts to lowercase
- `length()`: Returns string length
- `reverse()`: Returns a reversed copy of the string

### Collection Methods
- `length()`: Returns length of string, list, or hash
- `reverse()`: Reverses the elements of a list or string

### List Methods
- `push(value: dynamic) -> list`: Adds an element to the end of the list and returns the modified list
- `empty() -> list`: Removes all elements from the list and returns the empty list
- `clone() -> list`: Returns a copy of the list
- `countOf(value: dynamic) -> int`: Returns the number of occurrences of a value in the list
- `find(value: dynamic) -> int`: Returns the index of the first occurrence of a value, or raises an error if not found
- `insertAt(index: int, value: dynamic) -> list`: Inserts a value at the specified index and returns the modified list
- `pull([index: int]) -> dynamic`: Removes and returns the element at the specified index (or the last element if no index is provided)
- `removeValue(value: dynamic) -> list`: Removes the first occurrence of a value and returns the modified list
- `order() -> list`: Sorts the list in place and returns the sorted list
- `merge(other: list) -> list`: Merges another list into the current list and returns the modified list
- `reverse() -> list`: Reverses the list in place and returns the reversed list

## Advanced Features

### Method Chaining
Methods can be chained for concise code.

### String Interpolation
Supports embedding expressions in strings using ${expression} syntax.

## Best Practices and Edge Cases

### 1. Input Validation

Always validate user input to ensure it meets the expected format and constraints:

```c
// Age input with validation
age_input: str = ask("Please enter your age: ");
user_age: int = 0;
if age_input.length() > 0 {
    user_age = age_input.asInt();
    if user_age <= 0 {
        say("Error: Age must be a positive number");
        user_age = 18; // Default value
    }
} else {
    say("Error: Age input is empty");
    user_age = 18; // Default value
}
```

### 2. Error Handling

Implement error handling for potential issues:

```c
// Division by zero handling
divisor: int = 0;
if divisor == 0 {
    say("Error: Cannot divide by zero");
} else {
    result = 10 / divisor;
    say("10 /", divisor, "=", result);
}
```

### 3. Empty Value Handling

Handle empty values appropriately:

```c
// Empty string handling
empty_str: str = "";
say("Empty string length:", empty_str.length());
say("Empty string trimmed:", empty_str.trim());

// Empty list handling
empty_list: list = [];
say("Empty list length:", empty_list.length());

// Empty hash handling
empty_hash: hash = {};
say("Empty hash keys:", empty_hash.keys());
say("Empty hash values:", empty_hash.values());
say("Empty hash length:", empty_hash.length());
```

### 4. Type Conversion Validation

Validate type conversions to prevent errors:

```c
str_num: str = "123";
num: int = 0;
if str_num.length() > 0 {
    num = str_num.asInt();
    say("String to Int:", num);
} else {
    say("Error: Empty string cannot be converted to integer");
}

// Invalid type conversion examples
invalid_int: str = "abc";
say("Attempting to convert 'abc' to integer:");
if invalid_int.length() > 0 {
    say("This would cause an error in a real application");
}
```

### 5. Method Chaining Validation

Validate method chaining to prevent errors:

```c
input_str: str = ask("Enter a number: ");
if input_str.length() > 0 {
    trimmed_input: str = input_str.trim();
    if trimmed_input.length() > 0 {
        result = trimmed_input.asInt();
        say("Processed input:", result);
    } else {
        say("Error: Input contains only whitespace");
    }
} else {
    say("Error: Empty input");
}
```

### 6. Function Return Values

Always return a value from functions:

```c
fn process_list(items: list) -> bool {
    if items.length() == 0 {
        say("List is empty");
        return false;
    }
    
    foreach item in items {
        say("Processing:", item);
    }
    return true;
}
```

### 7. Boundary Testing

Test boundary conditions to ensure robustness:

```c
// Age classification with boundary testing
if user_age > 18 {
    say("User is an adult.");
} else if user_age == 18 {
    say("User is exactly 18 years old.");
} else {
    say("User is a minor.");
}

// Maximum integer testing
max_int: int = 2147483647; // Maximum 32-bit integer
say("Maximum integer:", max_int);
say("Maximum integer + 1:", max_int + 1);
```

### 8. Null/Undefined Handling

Handle null/undefined values appropriately:

```c
// Null/undefined handling
say("Empty string is falsy:", empty_str.asBool() == false);
say("Empty list is falsy:", empty_list.asBool() == false);
say("Empty hash is falsy:", empty_hash.asBool() == false);
say("Zero is falsy:", 0.asBool() == false);
say("Non-zero is truthy:", 1.asBool() == true);
```

### 9. Dynamic Type Reassignment

Handle dynamic type changes safely:

```c
dynamic_var: dynamic = 42;
say("Dynamic variable:", dynamic_var);
say("Type of dynamic_var:", dynamic_var.type());

dynamic_var = "Now I'm a string!";
say("Dynamic variable:", dynamic_var);
say("Type of dynamic_var:", dynamic_var.type());
```

## Syntax Requirements

### 1. Semicolons

Every statement must end with a semicolon:

```c
// Correct
x: int = 10;
say("Hello");

// Incorrect - will cause syntax error
x: int = 10
say("Hello")
```

### 2. Function Return Values

Functions must return a value. Empty returns are not allowed:

```c
// Correct
fn process_list(items: list) -> bool {
    if items.length() == 0 {
        return false;
    }
    return true;
}

// Incorrect - will cause syntax error
fn process_list(items: list) -> bool {
    if items.length() == 0 {
        return;
    }
}
```

### 3. Method Calls

Method calls must be followed by parentheses, even if there are no arguments:

```c
// Correct
text.trim();
empty_list.length();

// Incorrect - will cause syntax error
text.trim;
empty_list.length;
```

### 4. Type Annotations

Type annotations are required for function parameters and variable declarations:

```c
// Correct
fn greet(name: str) -> void {
    say("Hello, ${name}!");
}
age: int = 25;

// Incorrect - will cause syntax error
fn greet(name) -> void {
    say("Hello, ${name}!");
}
age = 25;
```

## Variable Scoping and Mutability

Echo provides explicit control over variable scoping and mutability through the `use` and `use mut` statements. This feature ensures clear and safe access to global variables within functions.

### Basic Usage

```c
// Global variables
counter: int = 0;
name: str = "Global";
config: hash = {"enabled": true};

// Function with immutable access
fn readOnly() -> void {
    use counter;  // Read-only access to global counter
    say("Counter value:", counter);
}

// Function with mutable access
fn modifyCounter() -> void {
    use mut counter;  // Mutable access to global counter
    counter = counter + 1;
    say("Counter incremented:", counter);
}

// Multiple imports with nested function
fn multipleImports() -> void {
    use name;
    use counter;
    
    fn nestedGreet() -> void {
        use name;
        say("Hello from nested function,", name);
    }
    
    say("Name:", name);
    counter = counter + 1;
    nestedGreet();
}
```

### Key Features

1. **Explicit Imports**
   - Variables must be explicitly imported into function scope using `use`
   - Prevents accidental use of global variables
   - Makes dependencies clear and visible

2. **Mutability Control**
   - `use mut` allows modification of imported variables
   - Regular `use` provides read-only access
   - Prevents accidental modifications

3. **Shadowing Warning**
   - Local variables that shadow globals trigger warnings
   - Helps prevent naming conflicts
   - Makes code intent clearer

4. **Nested Scopes**
   - Inner functions can import variables from outer scopes
   - Maintains proper scoping rules
   - Supports complex nested function structures

### Best Practices

1. **Explicit Dependencies**
   - Always use `use` to make dependencies explicit
   - Makes code more maintainable and self-documenting
   - Helps prevent bugs from global state

2. **Mutability Control**
   - Use `use mut` only when you need to modify the variable
   - Prefer immutable imports by default
   - Makes code behavior more predictable

3. **Variable Shadowing**
   - Be mindful of variable shadowing in nested functions
   - Use clear naming to avoid conflicts
   - Consider using different names for local variables

4. **Code Safety**
   - Consider using immutable imports by default
   - Only use mutable imports when necessary
   - Makes code more robust and easier to reason about

### Error Cases

```c
fn errorExamples() -> void {
    // Error: Using global without import
    counter = 1;  // Will raise error

    // Error: Modifying immutable import
    use name;
    name = "New Name";  // Will raise error

    // Warning: Variable shadowing
    name: str = "Local";  // Will show warning
}
```

### Common Errors

1. **Missing Import**
   - Error: Using a global variable without `use`
   - Solution: Add `use` statement for the variable

2. **Immutable Modification**
   - Error: Modifying a variable imported with `use`
   - Solution: Use `use mut` if modification is needed

3. **Shadowing Warning**
   - Warning: Local variable shadows global
   - Solution: Use different name or acknowledge warning

### Examples

1. **Basic Counter**
```c
counter: int = 0;

fn increment() -> void {
    use mut counter;
    counter = counter + 1;
}

fn display() -> void {
    use counter;
    say("Current count:", counter);
}
```

2. **Configuration Management**
```c
config: hash = {
    "debug": true,
    "max_retries": 3
};

fn updateConfig() -> void {
    use mut config;
    config["max_retries"] = 5;
}

fn readConfig() -> void {
    use config;
    say("Debug mode:", config["debug"]);
}
```

3. **Nested Function Example**
```c
name: str = "Global";

fn outer() -> void {
    use name;
    
    fn inner() -> void {
        use name;
        say("Hello from inner:", name);
    }
    
    inner();
}
``` 

## Known Issues and Limitations

1. **Error Handling**: The language does not yet support try-catch blocks for exception handling.

2. **Null/Undefined Values**: The language does not have a dedicated null or undefined type. Empty strings, lists, and hashes can be used as alternatives.

3. **Type Validation**: There is limited validation for list element types and hash key/value types.

4. **Integer Overflow**: The language does not handle integer overflow gracefully.

## Future Improvements

1. **Error Handling**: Implement try-catch blocks for exception handling.

2. **Null/Undefined Values**: Add support for null and undefined values.

3. **Type Validation**: Enhance validation for list element types and hash key/value types.

4. **Integer Overflow**: Implement graceful handling for integer overflow.

5. **Default Values**: Add support for default values for optional parameters.

6. **Performance Optimization**: Optimize performance for large data structures and deeply nested function calls.

7. **Method Implementation**: Consolidate method implementations to avoid duplication between `execute_node` and `evaluate` methods.

8. **Syntax Error Handling**: Improve error messages for syntax errors to provide more helpful information.
