from functools import cmp_to_key


TYPE_MAP = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "hash": dict,
}

# Parameter name lists for built-in methods, used to support keyword arguments.
# Keys are method names; values are ordered param names for args *after* the implicit target
# (i.e., what the caller passes inside the parentheses when using method-call syntax).
BUILTIN_PARAMS = {
    "ask":         ["prompt"],
    "wait":        ["seconds"],
    "default":     ["fallback"],
    "asInt":       ["value"],
    "asFloat":     ["value"],
    "asBool":      ["value"],
    "asString":    ["value"],
    "type":        ["value"],
    "push":        ["value"],
    "insertAt":    ["index", "value"],
    "pull":        ["index"],
    "removeValue": ["value"],
    "find":        ["value"],
    "countOf":     ["value"],
    "order":       ["comparator"],
    "merge":       ["other"],
    "ensure":      ["key", "default"],
    "take":        ["key"],
}

# For built-ins that can also be called standalone (no target), the first arg is the target value.
_BUILTIN_STANDALONE_PARAMS = {
    "find":    ["items", "value"],
    "countOf": ["items", "value"],
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

    def resolve_function(self, name):
        current = self
        while current:
            func = current.functions.get(name)
            if func is not None:
                return func
            current = current.parent
        return None

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
        func = self.resolve_function(name)
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

    def call_function_with_values(self, name, arg_values, interpreter):
        func = self.resolve_function(name)
        if not func:
            raise Exception(f"Function '{name}' not defined")

        if len(arg_values) != len(func["params"]):
            raise TypeError(
                f"Function '{name}' expected {len(func['params'])} arguments, got {len(arg_values)}"
            )

        new_context = Context(parent=self)
        new_context.in_function = True
        new_context.functions["__current_function"] = name

        for index, param in enumerate(func["params"]):
            value = arg_values[index]
            param_type = func["param_types"].get(param)
            if param_type and not interpreter._matches_type(value, param_type):
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

        if func["return_type"]:
            if func["return_type"] == "void":
                if result is not None:
                    raise TypeError(f"Function '{name}' is declared as void but returns a value")
            elif not interpreter._matches_type(result, func["return_type"]):
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

    def _resolve_builtin_args(self, args, method_name, has_target):
        """Resolve keyword arguments for a built-in method call into positional order.

        If no keyword arguments are present the original list is returned unchanged.
        Raises TypeError for unknown keyword names, duplicates, or too many positional args.
        """
        has_keyword = any(
            isinstance(arg, dict) and arg.get("type") == "keyword_arg"
            for arg in args
        )
        if not has_keyword:
            return args

        # Variadic built-ins (say, format) do not have a fixed param list.
        if method_name in ("say", "format"):
            raise TypeError(f"{method_name}() does not support keyword arguments")

        # Pick the right param list depending on whether there is an implicit target.
        if not has_target and method_name in _BUILTIN_STANDALONE_PARAMS:
            params = _BUILTIN_STANDALONE_PARAMS[method_name]
        else:
            params = BUILTIN_PARAMS.get(method_name)

        if params is None:
            raise TypeError(f"{method_name}() does not support keyword arguments")

        positional = []
        keyword = {}
        for arg in args:
            if isinstance(arg, dict) and arg.get("type") == "keyword_arg":
                name = arg["name"]
                if name in keyword:
                    raise TypeError(f"{method_name}() got multiple values for argument '{name}'")
                if name not in params:
                    raise TypeError(f"{method_name}() got an unexpected keyword argument '{name}'")
                keyword[name] = arg["value"]
            else:
                positional.append(arg)

        slots = [None] * len(params)

        if len(positional) > len(params):
            raise TypeError(
                f"{method_name}() expected at most {len(params)} argument(s), got {len(positional)}"
            )
        for i, arg in enumerate(positional):
            slots[i] = arg

        for name, value_node in keyword.items():
            idx = params.index(name)
            if slots[idx] is not None:
                raise TypeError(f"{method_name}() got multiple values for argument '{name}'")
            slots[idx] = value_node

        # Strip trailing None slots (optional params that were not supplied).
        while slots and slots[-1] is None:
            slots = slots[:-1]

        # A None that is not at the tail means a required positional was skipped.
        for i, slot in enumerate(slots):
            if slot is None:
                raise TypeError(f"{method_name}() missing argument '{params[i]}'")

        return slots

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

    def _echo_type_name(self, value):
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "str"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "hash"
        return "dynamic"

    def _mutating_method_target_name(self, call, context):
        modifying_methods = {
            "push", "empty", "merge", "insertAt", "pull", "removeValue", "order", "wipe", "take", "take_last", "ensure"
        }

        if call["method"] not in modifying_methods:
            return None

        target_expr = call.get("target")
        if not isinstance(target_expr, dict) or target_expr.get("type") != "identifier":
            return None

        var_name = target_expr["name"]

        if context.in_function:
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

        return var_name

    def _target_or_first_arg(self, target_value, args, context, method_name):
        if target_value is not None:
            return target_value
        if not args:
            raise TypeError(f"{method_name}() requires a target or at least one argument")
        return self.evaluate(args[0], context)

    def _evaluate_method_call(self, call, context):
        has_target = "target" in call
        call = {**call, "args": self._resolve_builtin_args(call["args"], call["method"], has_target)}
        target_value = None
        if has_target:
            target_value = self.evaluate(call["target"], context)

        watched_var = self._mutating_method_target_name(call, context)
        is_watched = watched_var is not None and context.is_watched(watched_var)
        method = call["method"]

        if method == "say":
            values = [self.evaluate(arg, context) for arg in call["args"]]
            for i, value in enumerate(values):
                if i > 0:
                    print(" ", end="")
                print(self._stringify_value(value), end="")
            print()
            return None

        if method == "wait":
            duration = self.evaluate(call["args"][0], context)
            import time
            time.sleep(duration)
            return None

        if method == "ask":
            prompt = self._target_or_first_arg(target_value, call["args"], context, method)
            return input(prompt)

        if method == "asInt":
            return int(self._target_or_first_arg(target_value, call["args"], context, method))

        if method == "asFloat":
            return float(self._target_or_first_arg(target_value, call["args"], context, method))

        if method == "asBool":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(value, (str, list, dict)):
                return bool(len(value))
            if isinstance(value, (int, float)):
                return bool(value)
            return bool(value)

        if method == "asString":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            return self._stringify_value(value)

        if method == "type":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            return self._echo_type_name(value)

        if method == "default":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            fallback_arg = call["args"][0] if target_value is not None else call["args"][1]
            return value if value else self.evaluate(fallback_arg, context)

        if method == "trim":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if not isinstance(value, str):
                raise TypeError("trim() can only be called on strings")
            return value.strip()

        if method == "upperCase":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if not isinstance(value, str):
                raise TypeError("upperCase() can only be called on strings")
            return value.upper()

        if method == "lowerCase":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if not isinstance(value, str):
                raise TypeError("lowerCase() can only be called on strings")
            return value.lower()

        if method == "length":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(value, (str, list, dict)):
                return len(value)
            raise TypeError("length() can only be used on strings, lists, or hashes")

        if method == "keys":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(value, dict):
                return list(value.keys())
            raise TypeError("keys() can only be called on hashes")

        if method == "values":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(value, dict):
                return list(value.values())
            raise TypeError("values() can only be called on hashes")

        if method == "pairs":
            if not isinstance(target_value, dict):
                raise TypeError("pairs() can only be called on hashes")
            return [[k, v] for k, v in target_value.items()]

        if method == "reverse":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(value, str):
                return value[::-1]
            if isinstance(value, list):
                return value[::-1]
            raise TypeError("reverse() can only be called on strings or lists")

        if method == "format":
            value = self._target_or_first_arg(target_value, call["args"], context, method)
            if not isinstance(value, str):
                raise TypeError("format() can only be called on strings")
            return self._apply_string_format(value, call["args"], context)

        if method == "clone":
            target = self._target_or_first_arg(target_value, call["args"], context, method)
            if isinstance(target, list):
                return target.copy()
            if isinstance(target, dict):
                return target.copy()
            raise TypeError("clone() can only be called on lists or hashes")

        if method == "countOf":
            if target_value is not None:
                return self._count_of(target_value, call["args"], context)
            if len(call["args"]) != 2:
                raise TypeError("countOf(list, value) requires exactly two arguments when called without a target")
            target = self.evaluate(call["args"][0], context)
            return self._count_of(target, [call["args"][1]], context)

        if method == "find":
            target = self._target_or_first_arg(target_value, call["args"], context, method)
            if not isinstance(target, list):
                raise TypeError("find() can only be called on lists")
            value_arg = call["args"][0] if target_value is not None else call["args"][1]
            if target_value is None and len(call["args"]) != 2:
                raise TypeError("find(list, value) requires exactly two arguments when called without a target")
            if target_value is not None and len(call["args"]) != 1:
                raise TypeError("find() requires exactly one argument")
            value = self.evaluate(value_arg, context)
            try:
                return target.index(value)
            except ValueError:
                raise ValueError(f"Element {value} not found in list")

        if method in {"push", "empty", "insertAt", "pull", "removeValue", "order"}:
            if target_value is None:
                raise TypeError(f"{method}() must be called on a list target")
            result = self._apply_list_method(method, target_value, call["args"], context)
            if is_watched:
                self._watch_change(watched_var, target_value, context, f"modified by {method}() to")
            return result

        if method == "merge":
            if len(call["args"]) != 1:
                raise TypeError("merge() requires exactly one argument")
            other = self.evaluate(call["args"][0], context)
            result = self._apply_merge_method(target_value, other)
            if is_watched:
                self._watch_change(watched_var, target_value, context, "modified by merge() to")
            return result

        if method in {"wipe", "take", "take_last", "ensure"}:
            if target_value is None:
                raise TypeError(f"{method}() must be called on a hash target")
            evaluated_args = None
            if method == "take":
                key = self.evaluate(call["args"][0], context)
                evaluated_args = [key]
            elif method == "ensure":
                key = self.evaluate(call["args"][0], context)
                default_value = self.evaluate(call["args"][1], context)
                evaluated_args = [key, default_value]
            result = self._apply_hash_method(method, target_value, call["args"], context, evaluated_args=evaluated_args)
            if is_watched:
                self._watch_change(watched_var, target_value, context, f"modified by {method}() to")
            return result

        raise Exception(f"Unknown method: {method}")

    def _quote_string(self, value):
        escaped = value.replace("\\", "\\\\")
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\t", "\\t")
        escaped = escaped.replace("\r", "\\r")
        return f'"{escaped}"'

    def _stringify_value(self, value, nested=False):
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return self._quote_string(value) if nested else value
        if isinstance(value, list):
            return "[" + ", ".join(self._stringify_value(item, True) for item in value) + "]"
        if isinstance(value, dict):
            parts = []
            for key, item in value.items():
                parts.append(f"{self._stringify_value(key, True)}: {self._stringify_value(item, True)}")
            return "{" + ", ".join(parts) + "}"
        return str(value)

    def _apply_string_format(self, template, args, context):
        evaluated_args = [self.evaluate(arg, context) for arg in args]
        result = ""
        auto_index = 0
        i = 0

        while i < len(template):
            if template[i] == "{":
                if i + 1 < len(template) and template[i + 1] == "{":
                    result += "{"
                    i += 2
                    continue

                end = template.find("}", i + 1)
                if end == -1:
                    raise ValueError("format() string is missing a closing '}'")

                placeholder = template[i + 1:end].strip()
                if placeholder == "":
                    arg_index = auto_index
                    auto_index += 1
                else:
                    if not placeholder.isdigit():
                        raise ValueError("format() placeholders must be '{}' or numeric indexes like '{0}'")
                    arg_index = int(placeholder)

                if arg_index >= len(evaluated_args):
                    raise IndexError(f"format() placeholder index {arg_index} out of range")

                result += self._stringify_value(evaluated_args[arg_index])
                i = end + 1
                continue

            if template[i] == "}":
                if i + 1 < len(template) and template[i + 1] == "}":
                    result += "}"
                    i += 2
                    continue
                raise ValueError("format() encountered an unmatched '}'")

            result += template[i]
            i += 1

        return result

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
            if len(args) == 0:
                target.sort()
                return target

            if len(args) != 1:
                raise TypeError("order() accepts either no arguments or a single comparator function")

            comparator_name = None
            arg = args[0]
            if isinstance(arg, dict) and arg.get("type") == "identifier":
                if context.resolve_function(arg["name"]) is not None:
                    comparator_name = arg["name"]

            if comparator_name is None:
                comparator_name = self.evaluate(arg, context)
                if not isinstance(comparator_name, str):
                    raise TypeError("order() comparator must be a function name or string")

            comparator = context.resolve_function(comparator_name)
            if comparator is None:
                raise NameError(f"Comparator function '{comparator_name}' is not defined")
            if len(comparator["params"]) != 2:
                raise TypeError(f"Comparator function '{comparator_name}' must take exactly two arguments")

            def compare(left, right):
                result = context.call_function_with_values(comparator_name, [left, right], self)
                if not isinstance(result, int):
                    raise TypeError(f"Comparator function '{comparator_name}' must return int")
                return result

            target.sort(key=cmp_to_key(compare))
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
            return self._evaluate_method_call(node, context)

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
            return self._evaluate_method_call(expr, context)
        elif expr_type == "string_interpolation":
            return "".join(
                self._stringify_value(self.evaluate(part, context))
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