TYPE_MAP = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "hash": dict,
}

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    Console = None
    Panel = None

_RICH_WARNINGS_ENABLED = True


def set_rich_warnings_enabled(enabled: bool):
    global _RICH_WARNINGS_ENABLED
    _RICH_WARNINGS_ENABLED = enabled


def _print_warning(message: str):
    if _RICH_WARNINGS_ENABLED and Console is not None and Panel is not None:
        Console().print(Panel(message, title="Warning", border_style="yellow", expand=False))
        return

    print(f"Warning: {message}")

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
            current = self
            while current and current.in_function:
                if name in current.variables:
                    return current.variables[name]
                if name in current.imported_vars:
                    if current.parent is None:
                        raise NameError(f"Imported variable '{name}' not found in parent scope")
                    value = current.parent.get(name)
                    if value is None and not current.parent.is_variable_defined(name):
                        raise NameError(f"Imported variable '{name}' not found in parent scope")
                    return value
                current = current.parent

            raise NameError(f"Variable '{name}' used without 'use' statement in function")
            
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
            else:
                if var_type is None:
                    current = self
                    while current and current.in_function:
                        if name in current.variables:
                            current.variables[name] = value
                            return
                        current = current.parent

                    raise NameError(f"Cannot modify global variable '{name}' without 'use mut'")

                if name not in self.variables and self.parent and not self.parent.in_function and name in self.parent.variables:
                    _print_warning(f"Variable '{name}' shadows a global variable")
                    self.variables[name] = value
                    if var_type:
                        self.types[name] = var_type
                    return
        
        # For non-function contexts or local variables
        if name not in self.variables and self.parent:
            if var_type is None:
                # Updating an existing variable — walk the chain to find where it lives
                current = self.parent
                while current:
                    if name in current.variables:
                        # Found it — update in place
                        current.variables[name] = value
                        return
                    if current.in_function and name in current.imported_vars:
                        # It's a function's mutable import — let the function context handle it
                        current.set(name, value, var_type)
                        return
                    current = current.parent
                # Not found anywhere — fall through and create locally
            elif name in self.parent.variables:
                # New declaration shadows a parent variable — create locally
                pass

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

    def _bind_function_arguments(self, func_name, func, raw_args, interpreter):
        positional_args = []
        keyword_args = {}

        for arg in raw_args:
            if isinstance(arg, dict) and arg.get("type") == "keyword_arg":
                arg_name = arg["name"]
                if arg_name in keyword_args:
                    raise TypeError(f"Function '{func_name}' got multiple keyword arguments for '{arg_name}'")
                keyword_args[arg_name] = arg["value"]
            else:
                positional_args.append(arg)

        if len(positional_args) > len(func["params"]):
            raise TypeError(
                f"Function '{func_name}' expected at most {len(func['params'])} arguments, got {len(positional_args)}"
            )

        bound_arguments = {}

        for index, param in enumerate(func["params"][:len(positional_args)]):
            bound_arguments[param] = positional_args[index]

        for arg_name, arg_value in keyword_args.items():
            if arg_name not in func["params"]:
                raise TypeError(f"Function '{func_name}' got an unexpected keyword argument '{arg_name}'")
            if arg_name in bound_arguments:
                raise TypeError(f"Function '{func_name}' got multiple values for argument '{arg_name}'")
            bound_arguments[arg_name] = arg_value

        missing_params = [param for param in func["params"] if param not in bound_arguments]
        if missing_params:
            missing = missing_params[0]
            raise Exception(f"Missing argument for parameter '{missing}' in function '{func_name}'")

        return bound_arguments

    def call_function(self, name, args, interpreter):
        current = self
        func = None
        while current and func is None:
            func = current.functions.get(name)
            current = current.parent

        if not func:
            raise Exception(f"Function '{name}' not defined")

        # Create new context with current context as parent for closure support
        new_context = Context(parent=self)
        new_context.in_function = True  # Mark that we're inside a function
        new_context.functions["__current_function"] = name  # Track current function name

        bound_arguments = self._bind_function_arguments(name, func, args, interpreter)
        
        # Set parameters in the new context with type checking
        for param in func["params"]:
            value = interpreter.evaluate(bound_arguments[param], self)
            param_type = func["param_types"].get(param)
            
            if param_type:  # Only check type if it was specified
                if not interpreter._matches_type(value, param_type):
                    raise TypeError(
                        f"Argument '{param}' in function '{name}' must be of type "
                        f"{interpreter._format_type(param_type)}, got {type(value).__name__}"
                    )
            
            new_context.set(param, value, param_type)

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
                if not interpreter._matches_type(result, func["return_type"]):
                    raise TypeError(
                        f"Function '{name}' must return type {interpreter._format_type(func['return_type'])}, "
                        f"got {type(result).__name__}"
                    )

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

    def _inherit_context_flags(self, child_context, parent_context):
        child_context.in_function = parent_context.in_function
        if parent_context.in_loop:
            child_context.in_loop = True

        function_name = parent_context.functions.get("__current_function")
        if function_name is None:
            current = parent_context.parent
            while current and function_name is None:
                function_name = current.functions.get("__current_function")
                current = current.parent

        if function_name is not None:
            child_context.functions["__current_function"] = function_name

    def _format_type(self, type_spec):
        if isinstance(type_spec, str):
            return type_spec

        if isinstance(type_spec, dict) and type_spec.get("kind") == "object":
            fields = type_spec.get("fields", {})
            formatted_fields = []
            for field_name, field_type in fields.items():
                formatted_fields.append(f"{field_name}: {self._format_type(field_type)}")
            return "{ " + ", ".join(formatted_fields) + " }"

        return str(type_spec)

    def _matches_type(self, value, type_spec):
        if type_spec == "dynamic":
            return True

        if isinstance(type_spec, str):
            expected_python_type = TYPE_MAP.get(type_spec)
            if expected_python_type is None:
                return True
            return isinstance(value, expected_python_type)

        if isinstance(type_spec, dict) and type_spec.get("kind") == "object":
            if not isinstance(value, dict):
                return False

            for field_name, field_type in type_spec.get("fields", {}).items():
                if field_name not in value:
                    return False
                if not self._matches_type(value[field_name], field_type):
                    return False
            return True

        return True

    def _validate_declared_type(self, name, value, expected_type):
        if not self._matches_type(value, expected_type):
            raise TypeError(
                f"Cannot assign {type(value).__name__} to {self._format_type(expected_type)} variable '{name}'"
            )

    def _ensure_positional_args(self, args, call_name):
        for arg in args:
            if isinstance(arg, dict) and arg.get("type") == "keyword_arg":
                raise TypeError(f"{call_name} does not support keyword arguments")
        return args

    def _current_function_name(self, context):
        if not context.in_function:
            return "global"

        current = context
        while current:
            function_name = current.functions.get("__current_function")
            if function_name:
                return function_name
            current = current.parent
        return "unknown"

    def _watch_change(self, var_name, new_value, context, action="changed to"):
        print(f"WATCH: {var_name} {action} {new_value} (in {self._current_function_name(context)})")

    def _apply_list_method(self, method, target, args, context):
        if not isinstance(target, list):
            raise TypeError(f"{method}() can only be called on lists")

        if method == "push":
            if len(args) != 1:
                raise TypeError("push() requires exactly one argument")
            element = self.evaluate(args[0], context)
            target.append(element)
            return target

        if method == "empty":
            target.clear()
            return target

        if method == "insertAt":
            if len(args) != 2:
                raise TypeError("insertAt() requires exactly two arguments (index and value)")
            index = self.evaluate(args[0], context)
            if not isinstance(index, int):
                raise TypeError("insertAt() index must be an integer")
            if index < 0 or index > len(target):
                raise IndexError(f"Index {index} out of range for list of length {len(target)}")
            value = self.evaluate(args[1], context)
            target.insert(index, value)
            return target

        if method == "pull":
            if len(args) > 1:
                raise TypeError("pull() accepts at most one argument (index)")
            if len(args) == 1:
                index = self.evaluate(args[0], context)
                if not isinstance(index, int):
                    raise TypeError("pull() index must be an integer")
                if index < 0 or index >= len(target):
                    raise IndexError(f"Index {index} out of range for list of length {len(target)}")
                return target.pop(index)
            if not target:
                raise IndexError("Cannot pull from empty list")
            return target.pop()

        if method == "removeValue":
            if len(args) != 1:
                raise TypeError("removeValue() requires exactly one argument (value)")
            value = self.evaluate(args[0], context)
            try:
                target.remove(value)
                return target
            except ValueError:
                raise ValueError(f"Value {value} not found in list")

        if method == "order":
            target.sort()
            return target

        raise Exception(f"Unsupported list method in helper: {method}")

    def _apply_merge_method(self, target, other):
        if isinstance(target, list):
            if not isinstance(other, (list, str)):
                raise TypeError("merge() argument must be a list or string when merging lists")
            target.extend(other)
            return target
        if isinstance(target, dict):
            if not isinstance(other, dict):
                raise TypeError("merge() argument must be a hash when merging hashes")
            target.update(other)
            return target
        raise TypeError("merge() can only be called on lists or hashes")

    def _apply_hash_method(self, method, target, args, context, evaluated_args=None):
        if not isinstance(target, dict):
            raise TypeError(f"{method}() can only be called on hashes")

        if method == "wipe":
            target.clear()
            return target

        if method == "take":
            if len(args) != 1:
                raise TypeError("take() requires exactly one argument (key)")
            key = evaluated_args[0] if evaluated_args is not None else self.evaluate(args[0], context)
            if not isinstance(key, str):
                raise TypeError("take() key must be a string")
            if key not in target:
                raise KeyError(f"Key '{key}' not found in hash")
            value = target.pop(key)
            return [key, value]

        if method == "take_last":
            if not target:
                raise KeyError("Cannot take_last() from empty hash")
            key = list(target.keys())[-1]
            value = target.pop(key)
            return [key, value]

        if method == "ensure":
            if len(args) != 2:
                raise TypeError("ensure() requires exactly two arguments (key and default value)")
            key = evaluated_args[0] if evaluated_args is not None else self.evaluate(args[0], context)
            if not isinstance(key, str):
                raise TypeError("ensure() key must be a string")
            default_value = evaluated_args[1] if evaluated_args is not None else self.evaluate(args[1], context)
            if key not in target:
                target[key] = default_value
            return target[key]

        raise Exception(f"Unsupported hash method in helper: {method}")

    def _count_of(self, target, args, context):
        if not isinstance(target, list):
            raise TypeError("countOf() can only be called on lists")
        if len(args) != 1:
            raise TypeError("countOf() requires exactly one argument")
        value = self.evaluate(args[0], context)
        return target.count(value)

    def execute_node(self, node, context):
        node_type = node["type"]

        if node_type == "use_statement":
            self.execute_use_statement(node, context)
            return

        if node_type == "watch_statement":
            for var_name in node["variables"]:
                context.watch_variable(var_name)
            return

        if node_type == "index_assign":
            container = context.get(node["target"])
            if container is None:
                raise NameError(f"Variable '{node['target']}' is not defined")
            indices = node["indices"]
            inner = container
            for idx_expr in indices[:-1]:
                key = self.evaluate(idx_expr, context)
                inner = inner[key]
            final_key = self.evaluate(indices[-1], context)
            value = self.evaluate(node["value"], context)
            inner[final_key] = value
            context.set(node["target"], container)
            return

        if node_type == "assign":
            value = self.evaluate(node["value"], context)
            explicit_type = node.get("var_type")  # Type provided in code
            existing_type = context.get_type(node["target"])

            # Check if variable is being watched
            if context.is_watched(node["target"]):
                self._watch_change(node["target"], value, context)

            if explicit_type:
                # Only flag 'already declared' if the variable exists in THIS exact context
                local_type = context.types.get(node["target"])
                if local_type is not None and not context.in_function:
                    raise NameError(f"Variable '{node['target']}' is already declared")
                elif local_type is not None and context.in_function:
                    _print_warning(f"Variable '{node['target']}' shadows a global variable")

                self._validate_declared_type(node["target"], value, explicit_type)
                context.set(node["target"], value, explicit_type)

            else:
                if existing_type is None:
                    raise NameError(f"Variable '{node['target']}' is not declared")

                self._validate_declared_type(node["target"], value, existing_type)
                context.set(node["target"], value)

        elif node_type == "method_call":
            node = {**node, "args": self._ensure_positional_args(node["args"], f"{node['method']}()")}
            # # print(f"DEBUG: Method call in execute_node: {node['method']}")
            # List of methods that modify their target
            modifying_methods = {
                "push", "empty", "merge", "insertAt", "pull", "removeValue", "order", "wipe", "take", "take_last", "ensure"
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
                    else:
                        current = context
                        found_local = False
                        while current and current.in_function:
                            if var_name in current.variables:
                                found_local = True
                                break
                            current = current.parent

                        if not found_local:
                            raise NameError(f"Cannot modify global variable '{var_name}' without 'use mut'")

                if context.is_watched(var_name):
                    # Get the new value after the method call
                    if node["method"] == "push":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("push", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by push() to")
                        return result
                    elif node["method"] == "empty":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("empty", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by empty() to")
                        return result
                    elif node["method"] == "merge":
                        target = self.evaluate(node["target"], context)
                        if len(node["args"]) != 1:
                            raise TypeError("merge() requires exactly one argument")
                        other = self.evaluate(node["args"][0], context)
                        result = self._apply_merge_method(target, other)
                        self._watch_change(var_name, target, context, "modified by merge() to")
                        return result
                    elif node["method"] == "insertAt":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("insertAt", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by insertAt() to")
                        return result
                    elif node["method"] == "pull":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("pull", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by pull() to")
                        return result
                    elif node["method"] == "removeValue":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("removeValue", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by removeValue() to")
                        return result
                    elif node["method"] == "order":
                        target = self.evaluate(node["target"], context)
                        result = self._apply_list_method("order", target, node["args"], context)
                        self._watch_change(var_name, target, context, "modified by order() to")
                        return result

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
                return self._apply_list_method("push", target, node["args"], context)
            elif node["method"] == "empty":
                target = self.evaluate(node["target"], context)
                return self._apply_list_method("empty", target, node["args"], context)
            elif node["method"] == "clone":
                target = self.evaluate(node["target"], context)
                if isinstance(target, list):
                    return target.copy()
                elif isinstance(target, dict):
                    return target.copy()
                else:
                    raise TypeError("clone() can only be called on lists or hashes")
            elif node["method"] == "countOf":
                if "target" in node:
                    target = self.evaluate(node["target"], context)
                    return self._count_of(target, node["args"], context)
                if len(node["args"]) != 2:
                    raise TypeError("countOf(list, value) requires exactly two arguments when called without a target")
                target = self.evaluate(node["args"][0], context)
                return self._count_of(target, [node["args"][1]], context)
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
                return self._apply_list_method("insertAt", target, node["args"], context)
            elif node["method"] == "pull":
                target = self.evaluate(node["target"], context)
                return self._apply_list_method("pull", target, node["args"], context)
            elif node["method"] == "removeValue":
                target = self.evaluate(node["target"], context)
                return self._apply_list_method("removeValue", target, node["args"], context)
            elif node["method"] == "order":
                target = self.evaluate(node["target"], context)
                return self._apply_list_method("order", target, node["args"], context)
            # Hash methods
            elif node["method"] == "wipe":
                target = self.evaluate(node["target"], context)
                if "target" in node and isinstance(node["target"], dict) and node["target"]["type"] == "identifier":
                    var_name = node["target"]["name"]
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        print(f"WATCH: {var_name} modified by wipe() to {target} (in {function_name})")
                return self._apply_hash_method("wipe", target, node["args"], context)
            elif node["method"] == "take":
                target = self.evaluate(node["target"], context)
                key = self.evaluate(node["args"][0], context)
                if "target" in node and isinstance(node["target"], dict) and node["target"]["type"] == "identifier":
                    var_name = node["target"]["name"]
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        new_target = target.copy()
                        new_target.pop(key)
                        print(f"WATCH: {var_name} modified by take() to {new_target} (in {function_name})")
                return self._apply_hash_method("take", target, node["args"], context, evaluated_args=[key])
            elif node["method"] == "take_last":
                target = self.evaluate(node["target"], context)
                if "target" in node and isinstance(node["target"], dict) and node["target"]["type"] == "identifier":
                    var_name = node["target"]["name"]
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        # Create a copy of the target and remove the last key to show the new state
                        new_target = target.copy()
                        last_key = list(new_target.keys())[-1]
                        new_target.pop(last_key)
                        print(f"WATCH: {var_name} modified by take_last() to {new_target} (in {function_name})")
                return self._apply_hash_method("take_last", target, node["args"], context)
            elif node["method"] == "ensure":
                target = self.evaluate(node["target"], context)
                key = self.evaluate(node["args"][0], context)
                default_value = self.evaluate(node["args"][1], context)
                if "target" in node and isinstance(node["target"], dict) and node["target"]["type"] == "identifier":
                    var_name = node["target"]["name"]
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        # Create a copy of the target and add the key to show the new state
                        new_target = target.copy()
                        if key not in new_target:
                            new_target[key] = default_value
                        print(f"WATCH: {var_name} modified by ensure() to {new_target} (in {function_name})")
                return self._apply_hash_method("ensure", target, node["args"], context, evaluated_args=[key, default_value])

        elif node_type == "for":
            # Create a new context for the loop
            loop_context = Context(parent=context)
            loop_context.in_loop = True
            self._inherit_context_flags(loop_context, context)
            
            # Evaluate start, end, and step values (they could be numbers or variables)
            start = self.evaluate(node["start"], context) if isinstance(node["start"], dict) else node["start"]
            end = self.evaluate(node["end"], context) if isinstance(node["end"], dict) else node["end"]
            by = self.evaluate(node["by"], context) if isinstance(node["by"], dict) else node["by"]
            
            # Convert to int for iteration
            i = int(start)
            end = int(end)
            by = int(by)
            is_inclusive = node.get("inclusive", True)  # Default to inclusive if not specified
            
            # Get the expected type for the loop variable
            var_type = node["var_type"]
            
            # For loops must use int type for the loop variable
            if var_type != "int":
                raise TypeError(f"For loop variable must be of type int, got {var_type}")
            
            try:
                if by > 0:
                    while i < end or (is_inclusive and i == end):
                        if var_type == "int" and not isinstance(i, int):
                            raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                        iter_context = Context(parent=context)
                        iter_context.in_loop = True
                        self._inherit_context_flags(iter_context, context)
                        iter_context.set(node["var"], i, var_type)
                        try:
                            self.execute_block(node["body"], iter_context)
                        except ContinueException:
                            pass
                        i += by
                else:  # by < 0
                    while i > end or (is_inclusive and i == end):
                        if var_type == "int" and not isinstance(i, int):
                            raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                        iter_context = Context(parent=context)
                        iter_context.in_loop = True
                        self._inherit_context_flags(iter_context, context)
                        iter_context.set(node["var"], i, var_type)
                        try:
                            self.execute_block(node["body"], iter_context)
                        except ContinueException:
                            pass
                        i += by
            except BreakException:
                # Exit the loop
                pass

        elif node_type == "foreach":
            # Create a new context for the loop
            loop_context = Context(parent=context)
            loop_context.in_loop = True
            self._inherit_context_flags(loop_context, context)
            
            items = self.evaluate(node["iterable"], context)
            var_type = node["var_type"]
            
            try:
                for item in items:
                    # Check if the value matches the declared type
                    if var_type == "int" and not isinstance(item, int):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                    elif var_type == "float" and not isinstance(item, float):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                    elif var_type == "str" and not isinstance(item, str):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                    elif var_type == "bool" and not isinstance(item, bool):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                    elif var_type == "list" and not isinstance(item, list):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")
                    elif var_type == "hash" and not isinstance(item, dict):
                        raise TypeError(f"Loop variable {node['var']} must be of type {var_type}")

                    # Fresh context per iteration so body-local vars don't collide across runs
                    iter_context = Context(parent=context)
                    iter_context.in_loop = True
                    self._inherit_context_flags(iter_context, context)
                    iter_context.set(node["var"], item, var_type)
                    try:
                        self.execute_block(node["body"], iter_context)
                    except ContinueException:
                        # Just continue to the next iteration
                        pass
            except BreakException:
                # Exit the loop
                pass

        elif node_type == "while":
            try:
                while self.evaluate_condition(node["condition"], context):
                    iter_context = Context(parent=context)
                    iter_context.in_loop = True
                    self._inherit_context_flags(iter_context, context)
                    try:
                        self.execute_block(node["body"], iter_context)
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
                self._inherit_context_flags(if_context, context)
                self.execute_block(node["body"], if_context)
            elif node.get("else_body"):
                # Create a new context for the else block
                else_context = Context(parent=context)
                else_context.in_loop = context.in_loop
                self._inherit_context_flags(else_context, context)
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
            value = expr["value"]
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # Replace escape sequences
            value = value.replace('\\n', '\n')
            value = value.replace('\\t', '\t')
            value = value.replace('\\r', '\r')
            value = value.replace('\\"', '"')
            value = value.replace("\\'", "'")
            value = value.replace('\\\\', '\\')
            return value
        elif expr_type == "boolean":
            return expr["value"]
        elif expr_type == "null":
            return None
        elif expr_type == "identifier":
            name = expr["name"]
            value = context.get(name)
            if value is None and not context.is_variable_defined(name):
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
            op = expr["operator"]

            if op == "&&":
                left = self.evaluate(expr["left"], context)
                if not bool(left):
                    return False
                right = self.evaluate(expr["right"], context)
                return bool(right)

            if op == "||":
                left = self.evaluate(expr["left"], context)
                if bool(left):
                    return True
                right = self.evaluate(expr["right"], context)
                return bool(right)

            left = self.evaluate(expr["left"], context)
            right = self.evaluate(expr["right"], context)
            return self._binary_op(op, left, right)
        elif expr_type == "unary":
            operand = self.evaluate(expr["operand"], context)
            op = expr["operator"]
            return self._unary_op(op, operand)
        elif expr_type == "function_call":
            # # print(f"DEBUG: Method call in evaluate: {expr['method']}")
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
            expr = {**expr, "args": self._ensure_positional_args(expr["args"], f"{expr['method']}()")}
            # # print(f"DEBUG: Method call in evaluate: {expr['method']}")
            # Handle method calls on targets if they exist
            target_value = None
            if "target" in expr:
                target_value = self.evaluate(expr["target"], context)
            
            # Handle hash methods
            if expr["method"] == "pairs":
                if not isinstance(target_value, dict):
                    raise TypeError("pairs() can only be called on hashes")
                result = [[k, v] for k, v in target_value.items()]
                # # print(f"DEBUG evaluate: pairs() called on {target_value}, returning {result}")
                return result
            elif expr["method"] == "take":
                # print(f"DEBUG evaluate: take() called")
                target = self.evaluate(expr["target"], context)
                # print(f"DEBUG evaluate: take() target: {target}")
                if not isinstance(target, dict):
                    raise TypeError("take() can only be called on hashes")
                if len(expr["args"]) != 1:
                    raise TypeError("take() requires exactly one argument (key)")
                key = self.evaluate(expr["args"][0], context)
                # print(f"DEBUG evaluate: take() key: {key}")
                if not isinstance(key, str):
                    raise TypeError("take() key must be a string")
                if key not in target:
                    raise KeyError(f"Key '{key}' not found in hash")
                if "target" in expr and isinstance(expr["target"], dict) and expr["target"]["type"] == "identifier":
                    var_name = expr["target"]["name"]
                    # print(f"DEBUG evaluate: take() var_name: {var_name}")
                    # print(f"DEBUG evaluate: take() is_watched: {context.is_watched(var_name)}")
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        # print(f"DEBUG evaluate: take() function_name: {function_name}")
                        # Create a copy of the target and remove the key to show the new state
                        new_target = target.copy()
                        new_target.pop(key)
                        # print(f"DEBUG evaluate: take() new_target: {new_target}")
                        print(f"WATCH: {var_name} modified by take() to {new_target} (in {function_name})")
                return self._apply_hash_method("take", target, expr["args"], context, evaluated_args=[key])
            elif expr["method"] == "ask":
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
                return self._apply_list_method("push", target, expr["args"], context)
            elif expr["method"] == "empty":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                return self._apply_list_method("empty", target, expr["args"], context)
            elif expr["method"] == "clone":
                target = target_value if target_value is not None else self.evaluate(expr["args"][0], context)
                if isinstance(target, list):
                    return target.copy()
                elif isinstance(target, dict):
                    return target.copy()
                else:
                    raise TypeError("clone() can only be called on lists or hashes")
            elif expr["method"] == "countOf":
                if target_value is not None:
                    return self._count_of(target_value, expr["args"], context)
                if len(expr["args"]) != 2:
                    raise TypeError("countOf(list, value) requires exactly two arguments when called without a target")
                target = self.evaluate(expr["args"][0], context)
                return self._count_of(target, [expr["args"][1]], context)
            elif expr["method"] == "merge":
                if len(expr["args"]) != 1:
                    raise TypeError("merge() requires exactly one argument")
                other = self.evaluate(expr["args"][0], context)
                if "target" in expr and isinstance(expr["target"], dict) and expr["target"]["type"] == "identifier":
                    var_name = expr["target"]["name"]
                    if context.is_watched(var_name):
                        function_name = "global" if not context.in_function else context.functions.get("__current_function", "unknown")
                        print(f"WATCH: {var_name} modified by merge() to {target_value} (in {function_name})")
                return self._apply_merge_method(target_value, other)
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
                return self._apply_list_method("insertAt", target, expr["args"], context)
            elif expr["method"] == "pull":
                target = self.evaluate(expr["target"], context)
                return self._apply_list_method("pull", target, expr["args"], context)
            elif expr["method"] == "removeValue":
                target = self.evaluate(expr["target"], context)
                return self._apply_list_method("removeValue", target, expr["args"], context)
            elif expr["method"] == "order":
                target = self.evaluate(expr["target"], context)
                return self._apply_list_method("order", target, expr["args"], context)
            elif expr["method"] == "take_last":
                # Delegate to execute_node for watch tracking
                return self.execute_node({"type": "method_call", "method": "take_last", "target": expr["target"]}, context)
            elif expr["method"] == "ensure":
                # Delegate to execute_node for watch tracking
                return self.execute_node({"type": "method_call", "method": "ensure", "target": expr["target"], "args": expr["args"]}, context)
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
            if type(left) is int and type(right) is int:
                if right == 0:
                    raise ZeroDivisionError("integer division by zero")
                quotient = abs(left) // abs(right)
                if (left < 0) != (right < 0):
                    quotient = -quotient
                return quotient
            return left / right
        elif op == "%":
            if isinstance(left, int) and isinstance(right, int):
                if right == 0:
                    raise ZeroDivisionError("integer modulo by zero")
                quotient = abs(left) // abs(right)
                if (left < 0) != (right < 0):
                    quotient = -quotient
                return left - (quotient * right)
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
        elif op == "-":
            if not isinstance(operand, (int, float)):
                raise TypeError(f"Unary '-' requires a numeric operand, got {type(operand).__name__}")
            return -operand
        else:
            raise Exception(f"Unknown unary operator: {op}")

    def execute_use_statement(self, node, context):
        """Execute a use statement."""
        for var_name in node["variables"]:
            context.import_variable(var_name, node["is_mutable"])