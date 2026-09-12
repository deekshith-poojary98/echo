from echo.formatter import format_source
from echo.linter import lint_source
from helpers import assert_no_python_leak, run_echo


def test_named_function_is_a_value():
    result = run_echo(
        """
fn add(a: int, b: int) -> int {
    return a + b;
}
op: fn(int, int) -> int = add;
say(op(2, 3));
say(type(op));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["5", "fn"]


def test_function_value_in_a_list():
    result = run_echo(
        """
fn add(a: int, b: int) -> int {
    return a + b;
}
ops: list = [add];
say(ops[0](2, 3));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "5"


def test_lambda_block_and_inline():
    result = run_echo(
        """
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };
inc: fn(int) -> int = fn(x: int) -> int => x + 1;
say(double(21));
say(inc(41));
say(fn(x: int) -> int { return x - 1; }(10));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["42", "42", "9"]


def test_lambda_closes_over_outer_names():
    result = run_echo(
        """
factor: int = 3;
fn make() -> fn(int) -> int {
    return fn(x: int) -> int { return x * factor; };
}
scale: fn(int) -> int = make();
say(scale(4));
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "12"


def test_order_accepts_function_value_and_lambda():
    result = run_echo(
        """
fn descending(a: int, b: int) -> int {
    return b - a;
}
nums: list = [3, 1, 2];
nums.order(descending);
say(nums);
nums.order(fn(a: int, b: int) -> int { return a - b; });
say(nums);
nums.order("descending");
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[3, 2, 1]", "[1, 2, 3]", "[3, 2, 1]"]


def test_slice_syntax_matches_slice_method():
    result = run_echo(
        """
xs: list = [10, 20, 30, 40];
say(xs[1:3]);
say(xs.slice(1, 3));
say("Echo"[1:3]);
say(slice(items: xs, start: 0, end: 4));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[20, 30]", "[20, 30]", "ch", "[10, 20, 30, 40]"]


def test_slice_out_of_bounds_aborts():
    result = run_echo("say([1, 2][0:9]);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "slice()" in result.output
    assert "out of range" in result.output


def test_slice_requires_both_bounds():
    missing_end = run_echo("say([1, 2, 3][1:]);\n")
    missing_start = run_echo("say([1, 2, 3][:2]);\n")
    missing_both = run_echo("say([1, 2, 3][:]);\n")
    for result in (missing_end, missing_start, missing_both):
        assert result.exit_code == 1
        assert_no_python_leak(result)
        assert "Syntax Error" in result.output
        assert "bound" in result.output.lower()


def test_default_arguments_and_call_time_evaluation():
    result = run_echo(
        """
fn greet(name: str, punct: str = "!") {
    say("${name}${punct}");
}
greet("Echo");
greet("Echo", "?");
greet(name: "Hi", punct: ".");
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["Echo!", "Echo?", "Hi."]


def test_default_abort_still_aborts():
    skipped = run_echo(
        """
fn greet(name: str, punct: str = fail("unused")) {
    say(name);
}
greet("Echo", "!");
"""
    )
    assert skipped.exit_code == 0
    assert skipped.output.strip() == "Echo"

    aborted = run_echo(
        """
fn greet(name: str, punct: str = fail("nope")) {
    say(name);
}
greet("Echo");
"""
    )
    assert aborted.exit_code == 1
    assert_no_python_leak(aborted)
    assert "nope" in aborted.output


def test_variadic_user_function():
    result = run_echo(
        """
fn total(nums: int...) -> int {
    sum: int = 0;
    foreach n: int in nums {
        sum = sum + n;
    }
    return sum;
}
say(total());
say(total(1, 2, 3));
say(total(nums: [4, 5]));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["0", "6", "9"]


def test_defaults_and_variadic_together():
    result = run_echo(
        """
fn apply(mapper: fn(int) -> int, punct: str = ",", nums: int...) {
    parts: list = [];
    foreach v: int in nums {
        parts.push(mapper(v).asString());
    }
    say(parts.join(punct));
}
double: fn(int) -> int = fn(x: int) -> int { return x * 2; };
apply(double, nums: [1, 2, 3]);
apply(double, "-", 4, 5);
apply(mapper: double);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["2,4,6", "8-10", ""]


def test_missing_required_still_semantic_with_defaults():
    result = run_echo(
        """
fn greet(name: str, punct: str = "!") {
    say(name, punct);
}
greet();
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "name" in result.output


def test_extra_positional_without_variadic_is_semantic():
    result = run_echo(
        """
fn identity(a: int) -> int { return a; }
say(identity(1, 2));
"""
    )
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "expected at most 1 argument" in result.output


def test_check_fmt_lint_accept_new_syntax():
    source = """
fn apply(mapper: fn(int) -> int, punct: str = ",", nums: int...) {
    xs: list = [1, 2, 3, 4];
    say(xs[1:3]);
    say(mapper(2));
    say(punct);
    foreach v: int in nums {
        say(v);
    }
}
apply(fn(x: int) -> int { return x * 2; });
"""
    result = run_echo(source)
    assert result.exit_code == 0, result.output

    formatted = format_source(source)
    assert "fn(int) -> int" in formatted
    assert "punct: str = \",\"" in formatted
    assert "nums: int..." in formatted
    assert "xs[1:3]" in formatted
    assert format_source(formatted) == formatted

    findings = lint_source(formatted, filename="app.echo")
    assert findings == []


def test_map_named_fn_and_lambda():
    result = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}
nums: list = [1, 2, 3];
say(map(nums, double));
say(map(nums, fn(x: int) -> int { return x + 1; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 4, 6]", "[2, 3, 4]"]


def test_filter_named_fn_and_lambda():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}
nums: list = [1, 2, 3, 4];
say(filter(nums, even));
say(filter(nums, fn(x: int) -> bool { return x > 2; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 4]", "[3, 4]"]


def test_map_filter_empty_list():
    result = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}
fn keep(x: int) -> bool {
    return true;
}
empty: list = [];
say(map(empty, double));
say(filter(empty, keep));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[]"]


def test_map_filter_do_not_mutate_input():
    result = run_echo(
        """
nums: list = [1, 2, 3];
mapped: list = nums.map(fn(x: int) -> int { return x * 2; });
filtered: list = nums.filter(fn(x: int) -> bool { return x > 1; });
say(nums);
say(mapped);
say(filtered);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[2, 4, 6]", "[2, 3]"]


def test_map_filter_method_and_keyword_form():
    result = run_echo(
        """
fn triple(x: int) -> int {
    return x * 3;
}
fn odd(x: int) -> bool {
    return x % 2 == 1;
}
nums: list = [1, 2, 3];
say(nums.map(triple));
say(map(items: nums, f: triple));
say(nums.filter(odd));
say(filter(items: nums, f: odd));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[3, 6, 9]", "[3, 6, 9]", "[1, 3]", "[1, 3]"]


def test_filter_requires_bool_not_int():
    result = run_echo(
        """
say(filter([1, 0, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "filter()" in result.output
    assert "bool" in result.output


def test_map_filter_wrong_callback_type():
    not_fn = run_echo("say(map([1, 2], 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "map()" in not_fn.output
    assert "function" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> int {
    return a + b;
}
say(filter([1, 2], add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "filter()" in wrong_arity.output
    assert "one argument" in wrong_arity.output


def test_map_filter_callback_abort():
    mapped = run_echo(
        """
say(map([1, 2, 3], fn(x: int) -> int { return fail("mapped"); }));
"""
    )
    assert mapped.exit_code == 1
    assert_no_python_leak(mapped)
    assert "mapped" in mapped.output

    filtered = run_echo(
        """
say(filter([1, 2, 3], fn(x: int) -> bool { return fail("filtered"); }));
"""
    )
    assert filtered.exit_code == 1
    assert_no_python_leak(filtered)
    assert "filtered" in filtered.output


def test_reduce_named_fn_and_lambda():
    result = run_echo(
        """
fn add(acc: int, x: int) -> int {
    return acc + x;
}
fn concat(acc: str, item: str) -> str {
    return acc + item;
}
say(reduce([1, 2, 3], 0, add));
say(reduce([1, 2, 3], 10, fn(acc: int, x: int) -> int { return acc + x; }));
say(reduce(["a", "b", "c"], "", concat));
say(reduce(["a", "b"], "x", fn(acc: str, item: str) -> str { return acc + item; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["6", "16", "abc", "xab"]


def test_reduce_empty_list_returns_init_without_calling_f():
    result = run_echo(
        """
fn boom(acc: int, x: int) -> int {
    return fail("called");
}
empty: list = [];
say(reduce(empty, 10, boom));
say(reduce(empty, "init", fn(acc: str, x: str) -> str { return fail("called"); }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["10", "init"]


def test_reduce_do_not_mutate_input():
    result = run_echo(
        """
nums: list = [1, 2, 3];
total: int = nums.reduce(0, fn(acc: int, x: int) -> int { return acc + x; });
say(nums);
say(total);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "6"]


def test_reduce_method_and_keyword_form():
    result = run_echo(
        """
fn add(acc: int, x: int) -> int {
    return acc + x;
}
nums: list = [1, 2, 3];
say(nums.reduce(0, add));
say(reduce(items: nums, init: 0, f: add));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["6", "6"]


def test_reduce_wrong_callback_type():
    not_fn = run_echo("say(reduce([1, 2], 0, 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "reduce()" in not_fn.output
    assert "function" in not_fn.output
    assert "E2832" in not_fn.output

    wrong_arity = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}
say(reduce([1, 2], 0, double));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "reduce()" in wrong_arity.output
    assert "two arguments" in wrong_arity.output
    assert "E2833" in wrong_arity.output

    extra_default = run_echo(
        """
fn add3(acc: int, x: int, extra: int = 0) -> int {
    return acc + x + extra;
}
say(reduce([1, 2], 0, add3));
"""
    )
    assert extra_default.exit_code == 1
    assert_no_python_leak(extra_default)
    assert "two arguments" in extra_default.output
    assert "E2833" in extra_default.output


def test_reduce_callback_return_must_match_init():
    result = run_echo(
        """
say(reduce([1, 2], 0, fn(acc: int, x: int) -> str { return acc.asString(); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "reduce()" in result.output
    assert "E2834" in result.output


def test_reduce_callback_abort():
    result = run_echo(
        """
say(reduce([1, 2, 3], 0, fn(acc: int, x: int) -> int { return fail("reduced"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "reduced" in result.output


def test_foreach_named_fn_and_lambda_side_effects():
    result = run_echo(
        """
seen: list = [];
count: int = 0;
fn collect(x: int) -> int {
    use mut seen;
    seen.push(x);
    return x * 10;
}
say(forEach([1, 2, 3], collect));
say(seen);
[10, 20].forEach(fn(x: int) {
    use mut count;
    count = count + 1;
});
say(count);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "[1, 2, 3]", "2"]


def test_foreach_empty_list_returns_null_without_calling_f():
    result = run_echo(
        """
fn boom(x: int) -> int {
    return fail("called");
}
empty: list = [];
say(forEach(empty, boom));
say(forEach(empty, fn(x: int) -> int { return fail("called"); }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "null"]


def test_foreach_do_not_mutate_input():
    result = run_echo(
        """
nums: list = [1, 2, 3];
say(nums.forEach(fn(x: int) {}));
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "[1, 2, 3]"]


def test_foreach_method_and_keyword_form():
    result = run_echo(
        """
seen: list = [];
fn collect(x: int) {
    use mut seen;
    seen.push(x);
}
nums: list = [1, 2, 3];
say(nums.forEach(collect));
say(seen);
more: list = [];
fn keep(x: int) {
    use mut more;
    more.push(x);
}
say(forEach(items: nums, f: keep));
say(more);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["null", "[1, 2, 3]", "null", "[1, 2, 3]"]


def test_foreach_wrong_callback_type():
    not_fn = run_echo("say(forEach([1, 2], 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "forEach()" in not_fn.output
    assert "function" in not_fn.output
    assert "E2835" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> int {
    return a + b;
}
say(forEach([1, 2], add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "forEach()" in wrong_arity.output
    assert "one argument" in wrong_arity.output
    assert "E2836" in wrong_arity.output

    extra_default = run_echo(
        """
fn collect(x: int, extra: int = 0) {
    say(x);
}
say(forEach([1, 2], collect));
"""
    )
    assert extra_default.exit_code == 1
    assert_no_python_leak(extra_default)
    assert "one argument" in extra_default.output
    assert "E2836" in extra_default.output


def test_foreach_callback_abort():
    result = run_echo(
        """
say(forEach([1, 2, 3], fn(x: int) -> int { return fail("each"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "each" in result.output

