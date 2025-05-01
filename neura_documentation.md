# Neura Language Documentation

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
4. [Built-in Methods](#built-in-methods)
5. [Advanced Features](#advanced-features)
6. [Best Practices and Edge Cases](#best-practices-and-edge-cases)
7. [Syntax Requirements](#syntax-requirements)
8. [Known Issues and Limitations](#known-issues-and-limitations)
9. [Future Improvements](#future-improvements)

## Language Overview

Neura is a statically-typed programming language with dynamic capabilities. It supports various data types, control structures, and methods for data manipulation. The language emphasizes type safety while providing flexibility through dynamic typing when needed.

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
Every function must specify a return type using the `->` operator. Neura supports the following return types:
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
for i in 0..10 by 2 {
    say("Count:", i);
}

// Foreach loop
foreach item in items {
    say("Processing:", item);
}

// While loop
while condition {
    // code
}
```

### 4. Logical Operators

Neura supports three logical operators for boolean operations:

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
```

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

### Collection Methods
- `length()`: Returns length of string, list, or hash
- `keys()`: Returns list of hash keys
- `values()`: Returns list of hash values

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
