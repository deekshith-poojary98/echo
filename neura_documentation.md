# Neura Language Documentation

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
numbers: list = [1, 2, 3, 4, 5];
config: hash = {"debug": true, "port": 8080};
dynamic_var: dynamic = 42;

// Type checking
say("Type of x:", x.type());
say("Type of y:", y.type());
say("Type of name:", name.type());
```

### 2. Function Definitions

```c
// Standard function with block body and return type
fn process_user_data(age: int, is_active: bool, membership_duration: int) {
    // Input validation
    if age <= 0 {
        say("Error: Age must be a positive number");
        return 0;
    }
    
    if membership_duration < 0 {
        say("Error: Membership duration cannot be negative");
        return 0;
    }
    
    if is_active {
        if membership_duration >= 1 {
            return age * 1.5;  
        } else {
            return age * 1.2;  
        }
    } else {
        return age * 0.8;  
    }
}

// Inline function with arrow syntax
fn add(a: int, b: int) => a + b;
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
while counter < 5 {
    say("Counter:", counter);
    counter = counter + 1;
}
```

### 4. Methods

#### String Methods

- `trim()`: Removes whitespace from the beginning and end
- `upperCase()`: Converts to uppercase
- `lowerCase()`: Converts to lowercase
- `length()`: Returns the length of the string

#### Type Conversion Methods

- `asInt()`: Converts to integer
- `asFloat()`: Converts to float
- `asBool()`: Converts to boolean
- `asString()`: Converts to string
- `type()`: Returns the type of the value as a string

#### Hash Methods

- `keys()`: Returns a list of keys
- `values()`: Returns a list of values
- `length()`: Returns the number of key-value pairs

#### List Methods

- `length()`: Returns the number of elements

### 5. Input/Output

```c
// Output
say("Hello, World!");
say("Value:", some_variable);

// Input with validation
user_input: str = ask("Enter your name: ");
if user_input.length() == 0 {
    say("Error: Name cannot be empty");
    user_input = "Anonymous";
}
```

### 6. String Interpolation

```c
name: str = "John";
age: int = 30;
say("Name: ${name}, Age: ${age}");
```

### 7. Wait Function

```c
wait(1); // Waits for 1 second
say("waited 1 second");
```

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
fn process_list(items: list) {
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
fn process_list(items: list) {
    if items.length() == 0 {
        return false;
    }
    return true;
}

// Incorrect - will cause syntax error
fn process_list(items: list) {
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
fn greet(name: str) {
    say("Hello, ${name}!");
}
age: int = 25;

// Incorrect - will cause syntax error
fn greet(name) {
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
