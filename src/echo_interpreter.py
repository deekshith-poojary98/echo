import copy

class Context:
    def __init__(self, parent=None):
        self.variables = {}
        self.types = {}  # Store variable types
        self.functions = {}
        self.parent = parent  # For nested scopes
        self.in_loop = False  # Track if we're inside a loop
        self.in_function = False  # Track if we're inside a function
        self.imported_vars = {}  # Track imported variables and their mutability
        self.watched_vars = set()  # Track watched variables in this scope

    def watch_variable(self, name):
        """Add a variable to the watch list for this scope"""
        # Check if variable is defined in this scope or any parent scope
        if not self.is_variable_defined(name):
            raise NameError(f"Cannot watch undefined variable '{name}'")
        self.watched_vars.add(name)

    def is_variable_defined(self, name):
        """Check if a variable is defined in this scope or any parent scope"""
        if name in self.variables:
            return True
        if self.parent:
            return self.parent.is_variable_defined(name)
        return False

    def is_watched(self, name):
        """Check if a variable is being watched in this scope or any parent scope"""
        if name in self.watched_vars:
            return True
        if self.parent:
            return self.parent.is_watched(name)
        return False

    def get_watch_context(self, name):
        """Get the context where a variable is being watched"""
        if name in self.watched_vars:
            return self
        if self.parent:
            return self.parent.get_watch_context(name)
        return None

    def get(self, name):
        # If we're in a function, check if the variable is imported
        if self.in_function:
            if name not in self.imported_vars:
                # Check if it's a local variable
                if name in self.variables:
                    return self.variables[name]
                raise NameError(f"Variable '{name}' used without 'use' statement in function")
            
            # Get the value from parent context
            value = self.parent.get(name)
            if value is None:
                raise NameError(f"Imported variable '{name}' not found in parent scope")
            return value
            
        # For non-function contexts, check local then parent
        value = self.variables.get(name)
        if value is None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value, var_type=None):
        # If we're in a function, check if we can modify the variable
        if self.in_function:
            if name in self.imported_vars:
                if not self.imported_vars[name]:
                    raise NameError(f"Cannot modify immutable import '{name}', use 'use mut' to make it mutable")
                # Find the context where the variable is defined
                current = self
                while current:
                    if name in current.variables:
                        current.variables[name] = value
                        return
                    current = current.parent
            elif name not in self.variables and self.parent and name in self.parent.variables:
                # If we're declaring a new variable (has var_type), allow shadowing
                if var_type is not None:
                    print(f"Warning: Variable '{name}' shadows a global variable")
                    self.variables[name] = value
                    if var_type:
                        self.types[name] = var_type
                    return
                # Otherwise, it's an attempt to modify global without use mut
                raise NameError(f"Cannot modify global variable '{name}' without 'use mut'")
        
        # For non-function contexts or local variables
        if name not in self.variables and self.parent and name in self.parent.variables:
            self.parent.set(name, value)
            return
        
        self.variables[name] = value
        if var_type:
            self.types[name] = var_type

    def import_variable(self, name, is_mutable):
        if not self.in_function:
            raise SyntaxError("'use' statements can only be used inside functions")
        if name in self.imported_vars:
            raise SyntaxError(f"Variable '{name}' already imported")
            
        # Check the entire context chain for the variable
        current = self
        while current:
            if name in current.variables:
                # If we're in a nested function and the variable is already imported in a parent context
                if current != self and current.in_function and name in current.imported_vars:
                    # Inherit mutability from parent context
                    self.imported_vars[name] = current.imported_vars[name]
                else:
                    self.imported_vars[name] = is_mutable
                return
            current = current.parent
            
        raise NameError(f"Cannot import undefined variable '{name}'")

    def get_type(self, name):
        type_val = self.types.get(name)
        if type_val is None and self.parent:
            return self.parent.get_type(name)
        return type_val

    def define_function(self, name, params, body, inline, param_types=None, return_type=None):
        self.functions[name] = {
            "params": params,
            "body": body,
            "inline": inline,
            "param_types": param_types or {},  # Store parameter types, default to empty dict if not provided
            "return_type": return_type  # Store return type
        }

    def call_function(self, name, args, interpreter):
        func = self.functions.get(name)
        if not func and self.parent:
            func = self.parent.functions.get(name)
            
        if not func:
            raise Exception(f"Function '{name}' not defined")

        # Create new context with current context as parent for closure support
        new_context = Context(parent=self)
        new_context.in_function = True  # Mark that we're inside a function
        new_context.functions["__current_function"] = name  # Track current function name
        
        # Set parameters in the new context with type checking
        for i, param in enumerate(func["params"]):
            if i < len(args):
                value = interpreter.evaluate(args[i], self)
                param_type = func["param_types"].get(param)
                
                if param_type:  # Only check type if it was specified
                    # Type validation
                    type_map = {
                        "int": int,
                        "float": float,
                        "str": str,
                        "bool": bool,
                        "list": list,
                        "hash": dict,
                    }
                    
                    expected_type = type_map.get(param_type)
                    if expected_type and not isinstance(value, expected_type):
                        raise TypeError(f"Argument '{param}' in function '{name}' must be of type {param_type}, got {type(value).__name__}")
                
                new_context.set(param, value, param_type)
            else:
                raise Exception(f"Missing argument for parameter '{param}' in function '{name}'")

        if func["inline"]:
            result = interpreter.evaluate(func["body"], new_context)
        else:
            try:
                interpreter.execute_block(func["body"], new_context)
                result = None
            except ReturnValue as r:
                result = r.value

        # Validate return type if specified
        if func["return_type"]:
            if func["return_type"] == "void":
                if result is not None:
                    raise TypeError(f"Function '{name}' is declared as void but returns a value")
            else:
                type_map = {
                    "int": int,
                    "float": float,
                    "str": str,
                    "bool": bool,
                    "list": list,
                    "hash": dict,
                }
                
                expected_type = type_map.get(func["return_type"])
                if expected_type and not isinstance(result, expected_type):
                    raise TypeError(f"Function '{name}' must return type {func['return_type']}, got {type(result).__name__}")

        return result


class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    """Signal to break out of a loop."""
    pass


class ContinueException(Exception):
    """Signal to continue to the next iteration of a loop."""
    pass


class Interpreter:
    def __init__(self):
        self.context = Context()

    def execute(self, ast):
        for node in ast:
            self.execute_node(node, self.context)

    def execute_block(self, block, context):
        for node in block:
            self.execute_node(node, context)

    def execute_node(self, node, context):
        node_type = node["type"]

        if node_type == "use_statement":
            self.execute_use_statement(node, context)
            return

        if node_type == "watch_statement":
            for var_name in node["variables"]:
                context.watch_variable(var_name)
            return

        if node_type == "assign":
            value = self.evaluate(node["value"], context)
            explicit_type = node.get("var_type")  # Type provided in code
            existing_type = context.get_type(node["target"])

            # Map of declared types to Python types
            type_map = {
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "hash": dict,
            }

            def validate_type(name, value, expected_type):
                expected_python_type = type_map.get(expected_type)
                if expected_python_type and not isinstance(value, expected_python_type):
                    raise TypeError(f"Cannot assign {type(value).__name__} to {expected_type} variable '{name}'")

            # Check if variable is being watched
            if context.is_watched(node["target"]):
                watch_context = context.get_watch_context(node["target"])
                old_value = watch_context.get(node["target"])
                function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                print(f"WATCH: {node['target']} changed to {value} (in {function_name})")

            if explicit_type:
                if existing_type is not None and not context.in_function:
                    raise NameError(f"Variable '{node['target']}' is already declared")
                elif existing_type is not None and context.in_function:
                    print(f"Warning: Variable '{node['target']}' shadows a global variable")

                validate_type(node["target"], value, explicit_type)
                context.set(node["target"], value, explicit_type)

            else:
                if existing_type is None:
                    raise NameError(f"Variable '{node['target']}' is not declared")

                validate_type(node["target"], value, existing_type)
                context.set(node["target"], value)

        elif node_type == "method_call":
            # List of methods that modify their target
            modifying_methods = {
                "push", "empty", "merge", "insertAt", "pull", "removeValue", "order"
            }
            
            # Handle method calls with watch tracking
            if "target" in node and isinstance(node["target"], dict) and node["target"]["type"] == "identifier":
                var_name = node["target"]["name"]
                # Check if we're in a function and the method modifies the target
                if context.in_function and node["method"] in modifying_methods:
                    # Check if variable is imported
                    if var_name in context.imported_vars:
                        if not context.imported_vars[var_name]:
                            raise NameError(f"Cannot modify immutable import '{var_name}', use 'use mut' to make it mutable")
                    # Check if variable is global
                    elif var_name not in context.variables and context.parent and var_name in context.parent.variables:
                        raise NameError(f"Cannot modify global variable '{var_name}' without 'use mut'")

                if context.is_watched(var_name):
                    watch_context = context.get_watch_context(var_name)
                    old_value = watch_context.get(var_name)
                    function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                    
                    # Get the new value after the method call
                    if node["method"] == "push":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("push() can only be called on lists")
                        if len(node["args"]) != 1:
                            raise TypeError("push() requires exactly one argument")
                        element = self.evaluate(node["args"][0], context)
                        target.append(element)
                        print(f"WATCH: {var_name} modified by push() to {target} (in {function_name})")
                        return target
                    elif node["method"] == "empty":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("empty() can only be called on lists")
                        target.clear()
                        print(f"WATCH: {var_name} modified by empty() to {target} (in {function_name})")
                        return target
                    elif node["method"] == "merge":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("merge() can only be called on lists")
                        if len(node["args"]) != 1:
                            raise TypeError("merge() requires exactly one argument")
                        other = self.evaluate(node["args"][0], context)
                        if not isinstance(other, (list, str)):
                            raise TypeError("merge() argument must be a list or string")
                        target.extend(other)
                        print(f"WATCH: {var_name} modified by merge() to {target} (in {function_name})")
                        return target
                    elif node["method"] == "insertAt":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("insertAt() can only be called on lists")
                        if len(node["args"]) != 2:
                            raise TypeError("insertAt() requires exactly two arguments (index and value)")
                        index = self.evaluate(node["args"][0], context)
                        if not isinstance(index, int):
                            raise TypeError("insertAt() index must be an integer")
                        if index < 0 or index > len(target):
                            raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                        value = self.evaluate(node["args"][1], context)
                        target.insert(index, value)
                        print(f"WATCH: {var_name} modified by insertAt() to {target} (in {function_name})")
                        return target
                    elif node["method"] == "pull":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("pull() can only be called on lists")
                        if len(node["args"]) > 1:
                            raise TypeError("pull() accepts at most one argument (index)")
                        if len(node["args"]) == 1:
                            index = self.evaluate(node["args"][0], context)
                            if not isinstance(index, int):
                                raise TypeError("pull() index must be an integer")
                            if index < 0 or index >= len(target):
                                raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                            result = target.pop(index)
                            print(f"WATCH: {var_name} modified by pull() to {target} (in {function_name})")
                            return result
                        else:
                            if not target:
                                raise IndexError("Cannot pull from empty list")
                            result = target.pop()
                            print(f"WATCH: {var_name} modified by pull() to {target} (in {function_name})")
                            return result
                    elif node["method"] == "removeValue":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("removeValue() can only be called on lists")
                        if len(node["args"]) != 1:
                            raise TypeError("removeValue() requires exactly one argument (value)")
                        value = self.evaluate(node["args"][0], context)
                        try:
                            target.remove(value)
                            print(f"WATCH: {var_name} modified by removeValue() to {target} (in {function_name})")
                            return target
                        except ValueError:
                            raise ValueError(f"Value {value} not found in list")
                    elif node["method"] == "order":
                        target = self.evaluate(node["target"], context)
                        if not isinstance(target, list):
                            raise TypeError("order() can only be called on lists")
                        target.sort()
                        print(f"WATCH: {var_name} modified by order() to {target} (in {function_name})")
                        return target

            # Continue with normal method call handling if not watched or not a modifying method
            if node["method"] == "say":
                values = [self.evaluate(arg, context) for arg in node["args"]]
                # Print each value with proper formatting
                for i, value in enumerate(values):
                    if i > 0:
                        print(" ", end="")
                    print(value, end="")
                print()  # Add a newline at the end
            elif node["method"] == "wait":
                    # Get the duration in seconds
                    duration = self.evaluate(node["args"][0], context)
                    import time
                    time.sleep(duration)
            elif node["method"] == "ask":
                prompt = self.evaluate(node["args"][0], context)
                return input(prompt)
            elif node["method"] == "asInt":
                value = self.evaluate(node["args"][0], context)
                return int(value)
            elif node["method"] == "asFloat":
                value = self.evaluate(node["args"][0], context)
                return float(value)
            elif node["method"] == "asBool":
                value = self.evaluate(node["args"][0], context)
                if isinstance(value, (str, list, dict)):
                    return bool(len(value))  # Empty collections should be falsy
                elif isinstance(value, (int, float)):
                    return bool(value)  # Zero should be falsy, non-zero truthy
                return bool(value)  # Default case
            elif node["method"] == "asString":
                value = self.evaluate(node["args"][0], context)
                return str(value)
            elif node["method"] == "type":
                value = self.evaluate(node["args"][0], context)
                return type(value).__name__
            elif node["method"] == "trim":
                value = self.evaluate(node["args"][0], context)
                return value.strip()
            elif node["method"] == "upperCase":
                value = self.evaluate(node["args"][0], context)
                return value.upper()
            elif node["method"] == "lowerCase":
                value = self.evaluate(node["args"][0], context)
                return value.lower()
            elif node["method"] == "length":
                value = self.evaluate(node["args"][0], context)
                if isinstance(value, (str, list, dict)):
                    return len(value)
                raise TypeError("length() can only be used on strings, lists, or hashes")
            elif node["method"] == "keys":
                value = self.evaluate(node["args"][0], context)
                if isinstance(value, dict):
                    return list(value.keys())
                raise TypeError("keys() can only be called on hashes")
            elif node["method"] == "values":
                value = self.evaluate(node["args"][0], context)
                if isinstance(value, dict):
                    return list(value.values())
                raise TypeError("values() can only be called on hashes")
            elif node["method"] == "reverse":
                value = self.evaluate(node["args"][0], context)
                if isinstance(value, str):
                    return value[::-1]  # Reverse string using slice
                elif isinstance(value, list):
                    return value[::-1]  # Reverse list using slice
                raise TypeError("reverse() can only be called on strings or lists")
            elif node["method"] == "push":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("push() can only be called on lists")
                if len(node["args"]) != 1:
                    raise TypeError("push() requires exactly one argument")
                element = self.evaluate(node["args"][0], context)
                target.append(element)
                return target
            elif node["method"] == "empty":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("empty() can only be called on lists")
                target.clear()
                return target
            elif node["method"] == "clone":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("clone() can only be called on lists")
                return target.copy()
            elif node["method"] == "countOf":
                target = self.evaluate(node["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("countOf() can only be called on lists")
                if len(node["args"]) != 1:
                    raise TypeError("countOf() requires exactly one argument")
                value = self.evaluate(node["args"][0], context)
                return target.count(value)
            elif node["method"] == "merge":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("merge() can only be called on lists")
                if len(node["args"]) != 1:
                    raise TypeError("merge() requires exactly one argument")
                other = self.evaluate(node["args"][0], context)
                if not isinstance(other, (list, str)):
                    raise TypeError("merge() argument must be a list or string")
                # Modify the target list in place by extending it
                target.extend(other)
                return target
            elif node["method"] == "find":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("find() can only be called on lists")
                if len(node["args"]) != 1:
                    raise TypeError("find() requires exactly one argument")
                value = self.evaluate(node["args"][0], context)
                try:
                    return target.index(value)
                except ValueError:
                    raise ValueError(f"Element {value} not found in list")
            elif node["method"] == "insertAt":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("insertAt() can only be called on lists")
                if len(node["args"]) != 2:
                    raise TypeError("insertAt() requires exactly two arguments (index and value)")
                index = self.evaluate(node["args"][0], context)
                if not isinstance(index, int):
                    raise TypeError("insertAt() index must be an integer")
                if index < 0 or index > len(target):
                    raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                value = self.evaluate(node["args"][1], context)
                target.insert(index, value)
                return target
            elif node["method"] == "pull":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("pull() can only be called on lists")
                if len(node["args"]) > 1:
                    raise TypeError("pull() accepts at most one argument (index)")
                if len(node["args"]) == 1:
                    index = self.evaluate(node["args"][0], context)
                    if not isinstance(index, int):
                        raise TypeError("pull() index must be an integer")
                    if index < 0 or index >= len(target):
                        raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                    return target.pop(index)
                else:
                    if not target:
                        raise IndexError("Cannot pull from empty list")
                    return target.pop()
            elif node["method"] == "removeValue":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("removeValue() can only be called on lists")
                if len(node["args"]) != 1:
                    raise TypeError("removeValue() requires exactly one argument (value)")
                value = self.evaluate(node["args"][0], context)
                try:
                    target.remove(value)
                    return target
                except ValueError:
                    raise ValueError(f"Value {value} not found in list")
            elif node["method"] == "order":
                target = self.evaluate(node["target"], context)
                if not isinstance(target, list):
                    raise TypeError("order() can only be called on lists")
                target.sort()
                return target

        elif node_type == "for":
            # Create a new context for the loop
            loop_context = Context(parent=context)
            loop_context.in_loop = True
            
            # Evaluate start, end, and step values (they could be numbers or variables)
            start = self.evaluate(node["start"], context) if isinstance(node["start"], dict) else node["start"]
            end = self.evaluate(node["end"], context) if isinstance(node["end"], dict) else node["end"]
            by = self.evaluate(node["by"], context) if isinstance(node["by"], dict) else node["by"]
            
            # Convert to int for iteration
            i = int(start)
            end = int(end)
            by = int(by)
            is_inclusive = node.get("inclusive", True)  # Default to inclusive if not specified
            
            try:
                if by > 0:
                    while i < end or (is_inclusive and i == end):
                        loop_context.set(node["var"], i)
                        try:
                            self.execute_block(node["body"], loop_context)
                        except ContinueException:
                            # Just continue to the next iteration
                            pass
                        i += by
                else:  # by < 0
                    while i > end or (is_inclusive and i == end):
                        loop_context.set(node["var"], i)
                        try:
                            self.execute_block(node["body"], loop_context)
                        except ContinueException:
                            # Just continue to the next iteration
                            pass
                        i += by
            except BreakException:
                # Exit the loop
                pass

        elif node_type == "foreach":
            # Create a new context for the loop
            loop_context = Context(parent=context)
            loop_context.in_loop = True
            
            items = self.evaluate(node["iterable"], context)
            try:
                for item in items:
                    loop_context.set(node["var"], item)
                    try:
                        self.execute_block(node["body"], loop_context)
                    except ContinueException:
                        # Just continue to the next iteration
                        pass
            except BreakException:
                # Exit the loop
                pass

        elif node_type == "while":
            # Create a new context for the loop
            loop_context = Context(parent=context)
            loop_context.in_loop = True
            
            try:
                while self.evaluate_condition(node["condition"], context):
                    try:
                        self.execute_block(node["body"], loop_context)
                    except ContinueException:
                        # Just continue to the next iteration
                        pass
            except BreakException:
                # Exit the loop
                pass

        elif node_type == "if":
            if self.evaluate_condition(node["condition"], context):
                # Create a new context for the if block
                if_context = Context(parent=context)
                if_context.in_loop = context.in_loop
                self.execute_block(node["body"], if_context)
            elif node.get("else_body"):
                # Create a new context for the else block
                else_context = Context(parent=context)
                else_context.in_loop = context.in_loop
                self.execute_block(node["else_body"], else_context)

        elif node_type == "func_def":
            context.define_function(
                node["name"],
                node["params"],
                node["body"],
                node["inline"],
                node.get("param_types", {}),  # Pass parameter types
                node.get("return_type")  # Pass return type
            )

        elif node_type == "function_call":
            return context.call_function(node["name"], node["args"], self)
        
        elif node_type == "return":
            if not context.in_function and not any(parent.in_function for parent in self._get_parent_contexts(context)):
                raise SyntaxError("'return' statement outside function")
            value = self.evaluate(node["value"], context) if node.get("value") else None
            raise ReturnValue(value)
            
        elif node_type == "break":
            if not context.in_loop and not any(parent.in_loop for parent in self._get_parent_contexts(context)):
                raise SyntaxError("'break' statement outside loop")
            raise BreakException()
            
        elif node_type == "continue":
            if not context.in_loop and not any(parent.in_loop for parent in self._get_parent_contexts(context)):
                raise SyntaxError("'continue' statement outside loop")
            raise ContinueException()

    def _get_parent_contexts(self, context):
        """Helper to get all parent contexts."""
        parents = []
        current = context.parent
        while current:
            parents.append(current)
            current = current.parent
        return parents

    def evaluate_condition(self, condition, context):
        """Evaluate a condition expression to a boolean value."""
        result = self.evaluate(condition, context)
        # Convert result to boolean if needed
        return bool(result)

    def evaluate(self, expr, context):
        expr_type = expr["type"]

        if expr_type == "int":
            # Convert to int and raise error if it's a float
            value = float(expr["value"])
            if value.is_integer():
                return int(value)
            raise TypeError(f"Cannot convert {expr['value']} to integer")
        elif expr_type == "float":
            return float(expr["value"])
        elif expr_type == "string":
            # Process escape sequences in string literals
            value = expr["value"].strip('"')
            # Replace escape sequences
            value = value.replace('\\n', '\n')
            value = value.replace('\\t', '\t')
            value = value.replace('\\r', '\r')
            value = value.replace('\\"', '"')
            value = value.replace('\\\\', '\\')
            return value
        elif expr_type == "boolean":
            return expr["value"]
        elif expr_type == "identifier":
            value = context.get(expr["name"])
            if value is None:
                raise NameError(f"Variable '{expr['name']}' is not defined")
            return value
        elif expr_type == "list":
            return [self.evaluate(e, context) for e in expr["elements"]]
        elif expr_type == "hash":
            return {
                pair["key"]: self.evaluate(pair["value"], context)
                for pair in expr["pairs"]
            }
        elif expr_type == "binary":
            left = self.evaluate(expr["left"], context)
            right = self.evaluate(expr["right"], context)
            op = expr["operator"]
            return self._binary_op(op, left, right)
        elif expr_type == "unary":
            operand = self.evaluate(expr["operand"], context)
            op = expr["operator"]
            return self._unary_op(op, operand)
        elif expr_type == "function_call":
            return context.call_function(expr["name"], expr["args"], self)
        elif expr_type == "index":
            target = self.evaluate(expr["target"], context)
            index = self.evaluate(expr["index"], context)
            
            if isinstance(target, dict):
                if not isinstance(index, str):
                    raise TypeError(f"Hash key must be a string, got {type(index).__name__}")
                if index not in target:
                    raise KeyError(f"Key '{index}' not found in hash")
                return target[index]
            elif isinstance(target, str):
                if not isinstance(index, int):
                    raise TypeError(f"String index must be an integer, got {type(index).__name__}")
                if index < 0 or index >= len(target):
                    raise IndexError(f"String index {index} out of range")
                return target[index]
            elif isinstance(target, list):
                if not isinstance(index, int):
                    raise TypeError(f"List index must be an integer, got {type(index).__name__}")
                if index < 0 or index >= len(target):
                    raise IndexError(f"List index {index} out of range")
                return target[index]
            else:
                raise TypeError(f"Cannot index type {type(target).__name__}")
        elif expr_type == "method_call":
            # Handle method calls on targets if they exist
            target_value = None
            if "target" in expr:
                target_value = self.evaluate(expr["target"], context)
            
            if expr["method"] == "ask":
                return input(self.evaluate(expr["args"][0], context))
            elif expr["method"] == "asInt":
                value = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                return int(value)
            elif expr["method"] == "asFloat":
                value = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                return float(value)
            elif expr["method"] == "asBool":
                value = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(value, (str, list, dict)):
                    return bool(len(value))  # Empty collections should be falsy
                elif isinstance(value, (int, float)):
                    return bool(value)  # Zero should be falsy, non-zero truthy
                return bool(value)  # Default case
            elif expr["method"] == "asString":
                value = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                return str(value)
            elif expr["method"] == "type":
                value = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(value, bool):
                    return "bool"
                elif isinstance(value, int):
                    return "int"
                elif isinstance(value, float):
                    return "float"
                elif isinstance(value, str):
                    return "str"
                elif isinstance(value, list):
                    return "list"
                elif isinstance(value, dict):
                    return "hash"
                else:
                    return "dynamic"
            elif expr["method"] == "default":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                return val if val else self.evaluate(expr["args"][1], context)
            elif expr["method"] == "trim":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(val, str):
                    raise TypeError("trim() can only be called on strings")
                return val.strip()
            elif expr["method"] == "upperCase":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(val, str):
                    raise TypeError("upperCase() can only be called on strings")
                return val.upper()
            elif expr["method"] == "lowerCase":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(val, str):
                    raise TypeError("lowerCase() can only be called on strings")
                return val.lower()
            elif expr["method"] == "length":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(val, (str, list, dict)):
                    return len(val)
                raise TypeError("length() can only be used on strings, lists, or hashes")  
            elif expr["method"] == "keys":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(val, dict):
                    return list(val.keys())
                raise TypeError("keys() can only be called on hashes")
            elif expr["method"] == "values":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(val, dict):
                    return list(val.values())
                raise TypeError("values() can only be called on hashes")
            elif expr["method"] == "reverse":
                val = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(val, str):
                    return val[::-1]  # Reverse string using slice
                elif isinstance(val, list):
                    return val[::-1]  # Reverse list using slice
                raise TypeError("reverse() can only be called on strings or lists")
            elif expr["method"] == "push":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("push() can only be called on lists")
                if len(expr["args"]) != 1:
                    raise TypeError("push() requires exactly one argument")
                element = self.evaluate(expr["args"][0], context)
                target.append(element)
                return target
            elif expr["method"] == "empty":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("empty() can only be called on lists")
                target.clear()
                return target
            elif expr["method"] == "clone":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("clone() can only be called on lists")
                return target.copy()
            elif expr["method"] == "countOf":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("countOf() can only be called on lists")
                if len(expr["args"]) != 1:
                    raise TypeError("countOf() requires exactly one argument")
                value = self.evaluate(expr["args"][0], context)
                return target.count(value)
            elif expr["method"] == "merge":
                target = self.evaluate(expr["target"], context)
                if not isinstance(target, list):
                    raise TypeError("merge() can only be called on lists")
                if len(expr["args"]) != 1:
                    raise TypeError("merge() requires exactly one argument")
                other = self.evaluate(expr["args"][0], context)
                if not isinstance(other, (list, str)):
                    raise TypeError("merge() argument must be a list or string")
                # Modify the target list in place by extending it
                target.extend(other)
                return target
            elif expr["method"] == "find":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if not isinstance(target, list):
                    raise TypeError("find() can only be called on lists")
                if len(expr["args"]) != 1:
                    raise TypeError("find() requires exactly one argument")
                value = self.evaluate(expr["args"][0], context)
                try:
                    return target.index(value)
                except ValueError:
                    raise ValueError(f"Element {value} not found in list")
            elif expr["method"] == "insertAt":
                target = self.evaluate(expr["target"], context)
                if not isinstance(target, list):
                    raise TypeError("insertAt() can only be called on lists")
                if len(expr["args"]) != 2:
                    raise TypeError("insertAt() requires exactly two arguments (index and value)")
                index = self.evaluate(expr["args"][0], context)
                if not isinstance(index, int):
                    raise TypeError("insertAt() index must be an integer")
                if index < 0 or index > len(target):
                    raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                value = self.evaluate(expr["args"][1], context)
                target.insert(index, value)
                return target
            elif expr["method"] == "pull":
                target = self.evaluate(expr["target"], context)
                if not isinstance(target, list):
                    raise TypeError("pull() can only be called on lists")
                if len(expr["args"]) > 1:
                    raise TypeError("pull() accepts at most one argument (index)")
                if len(expr["args"]) == 1:
                    index = self.evaluate(expr["args"][0], context)
                    if not isinstance(index, int):
                        raise TypeError("pull() index must be an integer")
                    if index < 0 or index >= len(target):
                        raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                    return target.pop(index)
                else:
                    if not target:
                        raise IndexError("Cannot pull from empty list")
                    return target.pop()
            elif expr["method"] == "removeValue":
                target = self.evaluate(expr["target"], context)
                if not isinstance(target, list):
                    raise TypeError("removeValue() can only be called on lists")
                if len(expr["args"]) != 1:
                    raise TypeError("removeValue() requires exactly one argument (value)")
                value = self.evaluate(expr["args"][0], context)
                try:
                    target.remove(value)
                    return target
                except ValueError:
                    raise ValueError(f"Value {value} not found in list")
            elif expr["method"] == "order":
                target = self.evaluate(expr["target"], context)
                if not isinstance(target, list):
                    raise TypeError("order() can only be called on lists")
                target.sort()
                return target
        elif expr_type == "string_interpolation":
            return "".join(
                str(self.evaluate(part, context))
                if part["type"] != "string"
                else part["value"]
                for part in expr["parts"]
            )
        
    def _binary_op(self, op, left, right):
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left / right
        elif op == "%":
            return left % right
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "<=":
            return left <= right
        elif op == ">=":
            return left >= right
        elif op == "&&":
            return bool(left) and bool(right)
        elif op == "||":
            return bool(left) or bool(right)
        else:
            raise Exception(f"Unknown operator: {op}")

    def _unary_op(self, op, operand):
        if op == "!":
            return not bool(operand)
        else:
            raise Exception(f"Unknown unary operator: {op}")

    def execute_use_statement(self, node, context):
        """Execute a use statement."""
        for var_name in node["variables"]:
            # Check if variable exists in parent scope
            if var_name not in context.parent.variables:
                raise RuntimeError(f"Variable '{var_name}' not found in parent scope")
            
            # Get the value from parent scope
            value = context.parent.variables[var_name]
            
            # If mutable, create a reference to the parent variable
            if node["is_mutable"]:
                context.variables[var_name] = value
            else:
                # If immutable, create a copy of the value
                if isinstance(value, (list, dict)):
                    context.variables[var_name] = copy.deepcopy(value)
                else:
                    context.variables[var_name] = value