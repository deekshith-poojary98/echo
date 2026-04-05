from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from echo_interpreter import Context, Interpreter


def ident(name: str) -> dict:
    return {"type": "identifier", "name": name}


def int_node(value: int) -> dict:
    return {"type": "int", "value": str(value)}


def str_node(value: str) -> dict:
    return {"type": "string", "value": f'"{value}"'}


def test_context_watch_lookup_and_parent_helpers():
    root = Context()
    root.set("count", 1, "int")
    child = Context(parent=root)
    grandchild = Context(parent=child)

    assert root.is_variable_defined("count") is True
    assert child.get("count") == 1

    root.watch_variable("count")
    assert grandchild.is_watched("count") is True
    assert grandchild.get_watch_context("count") is root
    assert grandchild.get_watch_context("missing") is None


def test_context_watch_undefined_raises():
    context = Context()

    with pytest.raises(NameError, match="Cannot watch undefined variable 'missing'"):
        context.watch_variable("missing")


def test_context_import_variable_errors_and_inheritance():
    root = Context()
    root.set("value", 1, "int")

    non_function = Context(parent=root)
    with pytest.raises(SyntaxError, match="'use' statements can only be used inside functions"):
        non_function.import_variable("value", True)

    func = Context(parent=root)
    func.in_function = True
    func.import_variable("value", False)
    with pytest.raises(SyntaxError, match="already imported"):
        func.import_variable("value", True)

    func.variables["value"] = 1
    func.types["value"] = "int"
    nested = Context(parent=func)
    nested.in_function = True
    nested.import_variable("value", True)
    assert nested.imported_vars["value"] is False

    missing = Context(parent=root)
    missing.in_function = True
    with pytest.raises(NameError, match="Cannot import undefined variable 'unknown'"):
        missing.import_variable("unknown", True)


def test_context_get_and_set_function_scope_errors():
    root = Context()
    root.set("x", 1, "int")

    func = Context(parent=root)
    func.in_function = True
    with pytest.raises(NameError, match="used without 'use' statement"):
        func.get("x")

    func.imported_vars["x"] = False
    with pytest.raises(NameError, match="Cannot modify immutable import 'x'"):
        func.set("x", 2)

    local_func = Context(parent=root)
    local_func.in_function = True
    with pytest.raises(NameError, match="Cannot modify global variable 'x' without 'use mut'"):
        local_func.set("x", 2)


def test_bind_function_arguments_errors():
    context = Context()
    interpreter = Interpreter()
    func = {"params": ["a", "b"]}

    with pytest.raises(TypeError, match="multiple keyword arguments"):
        context._bind_function_arguments(
            "demo",
            func,
            [
                {"type": "keyword_arg", "name": "a", "value": int_node(1)},
                {"type": "keyword_arg", "name": "a", "value": int_node(2)},
            ],
            interpreter,
        )

    with pytest.raises(TypeError, match="expected at most 2 arguments, got 3"):
        context._bind_function_arguments("demo", func, [int_node(1), int_node(2), int_node(3)], interpreter)

    with pytest.raises(TypeError, match="unexpected keyword argument 'c'"):
        context._bind_function_arguments(
            "demo",
            func,
            [{"type": "keyword_arg", "name": "c", "value": int_node(1)}],
            interpreter,
        )

    with pytest.raises(TypeError, match="multiple values for argument 'a'"):
        context._bind_function_arguments(
            "demo",
            func,
            [int_node(1), {"type": "keyword_arg", "name": "a", "value": int_node(2)}],
            interpreter,
        )

    with pytest.raises(Exception, match="Missing argument for parameter 'b'"):
        context._bind_function_arguments("demo", func, [int_node(1)], interpreter)


def test_call_function_and_call_function_with_values_type_and_return_validation():
    context = Context()
    interpreter = Interpreter()
    context.define_function(
        "add",
        ["a", "b"],
        {"type": "binary", "operator": "+", "left": ident("a"), "right": ident("b")},
        True,
        param_types={"a": "int", "b": "int"},
        return_type="int",
    )

    assert context.call_function("add", [int_node(2), int_node(3)], interpreter) == 5
    assert context.call_function_with_values("add", [2, 3], interpreter) == 5

    with pytest.raises(TypeError, match="must be of type int"):
        context.call_function("add", [str_node("x"), int_node(3)], interpreter)

    with pytest.raises(TypeError, match="expected 2 arguments, got 1"):
        context.call_function_with_values("add", [2], interpreter)

    context.define_function("bad_void", [], int_node(1), True, return_type="void")
    with pytest.raises(TypeError, match="declared as void but returns a value"):
        context.call_function("bad_void", [], interpreter)

    context.define_function("bad_return", [], str_node("x"), True, return_type="int")
    with pytest.raises(TypeError, match="must return type int"):
        context.call_function("bad_return", [], interpreter)


def test_interpreter_type_and_format_helpers():
    interpreter = Interpreter()
    object_type = {"kind": "object", "fields": {"id": "int", "name": "str"}}

    assert interpreter._format_type("int") == "int"
    assert interpreter._format_type(object_type) == "{ id: int, name: str }"
    assert interpreter._matches_type({"id": 1, "name": "Echo"}, object_type) is True
    assert interpreter._matches_type({"id": "x", "name": "Echo"}, object_type) is False
    assert interpreter._matches_type({"id": 1}, object_type) is False
    assert interpreter._matches_type("anything", "dynamic") is True
    assert interpreter._matches_type(1, "unknown-alias") is True


def test_interpreter_builtin_arg_resolution_and_name_helpers():
    interpreter = Interpreter()
    root = Context()
    child = Context(parent=root)
    child.in_function = True
    child.functions["__current_function"] = "demo"

    assert interpreter._resolve_builtin_args([int_node(1)], "push", True) == [int_node(1)]
    assert interpreter._resolve_builtin_args(
        [{"type": "keyword_arg", "name": "value", "value": int_node(3)}],
        "push",
        True,
    ) == [int_node(3)]

    with pytest.raises(TypeError, match=r"say\(\) does not support keyword arguments"):
        interpreter._resolve_builtin_args([{"type": "keyword_arg", "name": "value", "value": int_node(1)}], "say", True)

    with pytest.raises(TypeError, match="unexpected keyword argument 'wrong'"):
        interpreter._resolve_builtin_args([{"type": "keyword_arg", "name": "wrong", "value": int_node(1)}], "push", True)

    with pytest.raises(TypeError, match="multiple values for argument 'value'"):
        interpreter._resolve_builtin_args([int_node(1), {"type": "keyword_arg", "name": "value", "value": int_node(2)}], "push", True)

    with pytest.raises(TypeError, match="missing argument 'index'"):
        interpreter._resolve_builtin_args([{"type": "keyword_arg", "name": "value", "value": int_node(2)}], "insertAt", True)

    assert interpreter._current_function_name(root) == "global"
    assert interpreter._current_function_name(child) == "demo"
    assert interpreter._echo_type_name(True) == "bool"
    assert interpreter._echo_type_name(1) == "int"
    assert interpreter._echo_type_name(1.2) == "float"
    assert interpreter._echo_type_name("x") == "str"
    assert interpreter._echo_type_name([]) == "list"
    assert interpreter._echo_type_name({}) == "hash"
    assert interpreter._echo_type_name(object()) == "dynamic"


def test_target_stringify_and_format_helpers():
    interpreter = Interpreter()
    context = Context()
    context.set("name", "Echo", "str")

    with pytest.raises(TypeError, match=r"demo\(\) requires a target or at least one argument"):
        interpreter._target_or_first_arg(None, [], context, "demo")

    assert interpreter._target_or_first_arg("x", [], context, "demo") == "x"
    assert interpreter._target_or_first_arg(None, [str_node("Echo")], context, "demo") == "Echo"
    assert interpreter._quote_string('a\\b\n"c"') == '"a\\\\b\\n\\"c\\""'
    assert interpreter._stringify_value([True, None, {"name": "Echo"}]) == '[true, null, {"name": "Echo"}]'
    assert interpreter._apply_string_format("Hello, {}", [ident("name")], context) == "Hello, Echo"
    assert interpreter._apply_string_format("{{x}}", [], context) == "{x}"

    with pytest.raises(ValueError, match="missing a closing '}'"):
        interpreter._apply_string_format("{", [], context)
    with pytest.raises(ValueError, match=r"must be '\{\}' or numeric indexes"):
        interpreter._apply_string_format("{name}", [], context)
    with pytest.raises(IndexError, match="placeholder index 1 out of range"):
        interpreter._apply_string_format("{1}", [str_node("x")], context)
    with pytest.raises(ValueError, match="unmatched '}'"):
        interpreter._apply_string_format("}", [], context)


def test_list_hash_count_merge_binary_and_unary_helpers():
    interpreter = Interpreter()
    context = Context()
    context.define_function("cmp", ["a", "b"], {"type": "binary", "operator": "-", "left": ident("b"), "right": ident("a")}, True, param_types={"a": "int", "b": "int"}, return_type="int")
    context.define_function("cmp_bad_arity", ["a"], ident("a"), True, param_types={"a": "int"}, return_type="int")
    context.define_function("cmp_bad_return", ["a", "b"], str_node("x"), True, param_types={"a": "int", "b": "int"}, return_type="str")

    target = [3, 1, 2]
    assert interpreter._apply_list_method("push", target, [int_node(4)], context) == [3, 1, 2, 4]
    assert interpreter._apply_list_method("empty", target, [], context) == []

    with pytest.raises(TypeError, match=r"push\(\) requires exactly one argument"):
        interpreter._apply_list_method("push", [], [], context)
    with pytest.raises(TypeError, match=r"insertAt\(\) index must be an integer"):
        interpreter._apply_list_method("insertAt", [], [str_node("a"), int_node(1)], context)
    with pytest.raises(IndexError, match="Index -1 out of range"):
        interpreter._apply_list_method("insertAt", [], [int_node(-1), int_node(1)], context)
    with pytest.raises(TypeError, match=r"pull\(\) accepts at most one argument"):
        interpreter._apply_list_method("pull", [1], [int_node(0), int_node(1)], context)
    with pytest.raises(TypeError, match=r"pull\(\) index must be an integer"):
        interpreter._apply_list_method("pull", [1], [str_node("a")], context)
    with pytest.raises(IndexError, match="Index 3 out of range"):
        interpreter._apply_list_method("pull", [1], [int_node(3)], context)
    with pytest.raises(IndexError, match="Cannot pull from empty list"):
        interpreter._apply_list_method("pull", [], [], context)
    with pytest.raises(ValueError, match="Value 9 not found in list"):
        interpreter._apply_list_method("removeValue", [1], [int_node(9)], context)
    assert interpreter._apply_list_method("order", [3, 1, 2], [], context) == [1, 2, 3]
    assert interpreter._apply_list_method("order", [3, 1, 2], [ident("cmp")], context) == [3, 2, 1]

    with pytest.raises(TypeError, match="single comparator function"):
        interpreter._apply_list_method("order", [], [int_node(1), int_node(2)], context)
    with pytest.raises(TypeError, match="comparator must be a function name or string"):
        interpreter._apply_list_method("order", [], [int_node(1)], context)
    with pytest.raises(NameError, match="Comparator function 'missing' is not defined"):
        interpreter._apply_list_method("order", [], [str_node("missing")], context)
    with pytest.raises(TypeError, match="must take exactly two arguments"):
        interpreter._apply_list_method("order", [], [ident("cmp_bad_arity")], context)
    with pytest.raises(TypeError, match="must return int"):
        interpreter._apply_list_method("order", [2, 1], [ident("cmp_bad_return")], context)
    with pytest.raises(Exception, match="Unsupported list method"):
        interpreter._apply_list_method("unknown", [], [], context)

    assert interpreter._apply_merge_method([1], [2]) == [1, 2]
    assert interpreter._apply_merge_method(["a"], "bc") == ["a", "b", "c"]
    assert interpreter._apply_merge_method({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
    with pytest.raises(TypeError, match="must be a list or string"):
        interpreter._apply_merge_method([], 1)
    with pytest.raises(TypeError, match="must be a hash"):
        interpreter._apply_merge_method({}, [])
    with pytest.raises(TypeError, match="can only be called on lists or hashes"):
        interpreter._apply_merge_method(1, 2)

    assert interpreter._apply_hash_method("wipe", {"a": 1}, [], context) == {}
    assert interpreter._apply_hash_method("take", {"a": 1}, [str_node("a")], context) == ["a", 1]
    assert interpreter._apply_hash_method("take_last", {"a": 1}, [], context) == ["a", 1]
    assert interpreter._apply_hash_method("ensure", {}, [str_node("a"), int_node(3)], context) == 3

    with pytest.raises(TypeError, match="can only be called on hashes"):
        interpreter._apply_hash_method("wipe", [], [], context)
    with pytest.raises(TypeError, match="requires exactly one argument"):
        interpreter._apply_hash_method("take", {"a": 1}, [], context)
    with pytest.raises(TypeError, match="key must be a string"):
        interpreter._apply_hash_method("take", {"a": 1}, [int_node(1)], context)
    with pytest.raises(KeyError, match="Key 'missing' not found in hash"):
        interpreter._apply_hash_method("take", {"a": 1}, [str_node("missing")], context)
    with pytest.raises(KeyError, match=r"Cannot take_last\(\) from empty hash"):
        interpreter._apply_hash_method("take_last", {}, [], context)
    with pytest.raises(TypeError, match="requires exactly two arguments"):
        interpreter._apply_hash_method("ensure", {}, [str_node("a")], context)
    with pytest.raises(TypeError, match="key must be a string"):
        interpreter._apply_hash_method("ensure", {}, [int_node(1), int_node(2)], context)
    with pytest.raises(Exception, match="Unsupported hash method"):
        interpreter._apply_hash_method("unknown", {}, [], context)

    assert interpreter._count_of([1, 2, 1], [int_node(1)], context) == 2
    with pytest.raises(TypeError, match=r"countOf\(\) can only be called on lists"):
        interpreter._count_of({}, [int_node(1)], context)
    with pytest.raises(TypeError, match=r"countOf\(\) requires exactly one argument"):
        interpreter._count_of([], [], context)

    assert interpreter._binary_op("+", 1, 2) == 3
    assert interpreter._binary_op("/", 7, 2) == 3
    assert interpreter._binary_op("/", 7.0, 2) == 3.5
    assert interpreter._binary_op("%", -7, 3) == -1
    assert interpreter._binary_op("==", 1, 1) is True
    assert interpreter._binary_op("&&", 1, 0) is False
    assert interpreter._binary_op("||", 0, 1) is True
    with pytest.raises(ZeroDivisionError, match="integer division by zero"):
        interpreter._binary_op("/", 1, 0)
    with pytest.raises(ZeroDivisionError, match="integer modulo by zero"):
        interpreter._binary_op("%", 1, 0)
    with pytest.raises(Exception, match="Unknown operator"):
        interpreter._binary_op("???", 1, 2)

    assert interpreter._unary_op("!", 0) is True
    assert interpreter._unary_op("-", 3) == -3
    with pytest.raises(TypeError, match="requires a numeric operand"):
        interpreter._unary_op("-", "x")
    with pytest.raises(Exception, match="Unknown unary operator"):
        interpreter._unary_op("~", 1)


def test_execute_node_control_flow_helpers_and_warnings():
    interpreter = Interpreter()
    root = interpreter.context
    root.set("value", 1, "int")

    parents = interpreter._get_parent_contexts(Context(parent=Context(parent=root)))
    assert parents[-1] is root
    assert interpreter.evaluate_condition({"type": "boolean", "value": True}, root) is True

    with pytest.raises(SyntaxError, match="'return' statement outside function"):
        interpreter.execute_node({"type": "return", "value": None}, root)
    with pytest.raises(SyntaxError, match="'break' statement outside loop"):
        interpreter.execute_node({"type": "break"}, root)
    with pytest.raises(SyntaxError, match="'continue' statement outside loop"):
        interpreter.execute_node({"type": "continue"}, root)

    func_context = Context(parent=root)
    func_context.in_function = True
    with pytest.raises(Exception) as exc:
        interpreter.execute_node({"type": "return", "value": int_node(1)}, func_context)
    assert exc.value.__class__.__name__ == "ReturnValue"

    with pytest.raises(Exception) as exc:
        loop_context = Context(parent=root)
        loop_context.in_loop = True
        interpreter.execute_node({"type": "break"}, loop_context)
    assert exc.value.__class__.__name__ == "BreakException"

    with pytest.raises(Exception) as exc:
        loop_context = Context(parent=root)
        loop_context.in_loop = True
        interpreter.execute_node({"type": "continue"}, loop_context)
    assert exc.value.__class__.__name__ == "ContinueException"

    shadow_context = Context(parent=root)
    shadow_context.in_function = True
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        interpreter.execute_node({"type": "assign", "target": "value", "var_type": "int", "value": int_node(2)}, shadow_context)
    assert "Warning: Variable 'value' shadows a global variable" in stdout.getvalue()