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


def test_optional_slice_bounds_lists_and_strings():
    result = run_echo(
        """
xs: list = [10, 20, 30, 40];
s: str = "Echo";
say(xs[:]);
say(xs[1:]);
say(xs[:3]);
say(xs[1:3]);
say(s[:]);
say(s[1:]);
say(s[:3]);
say(s[1:3]);
say(xs[0]);
"""
    )
    assert result.exit_code == 0
    assert result.lines == [
        "[10, 20, 30, 40]",
        "[20, 30, 40]",
        "[10, 20, 30]",
        "[20, 30]",
        "Echo",
        "cho",
        "Ech",
        "ch",
        "10",
    ]


def test_empty_list_full_slice():
    result = run_echo("say([][:]);\n")
    assert result.exit_code == 0
    assert result.output.strip() == "[]"


def test_optional_slice_out_of_bounds_aborts():
    missing_end = run_echo("say([1, 2][9:]);\n")
    missing_start = run_echo("say([1, 2][:9]);\n")
    string_oob = run_echo('say("Echo"[9:]);\n')
    for result in (missing_end, missing_start, string_oob):
        assert result.exit_code == 1
        assert_no_python_leak(result)
        assert "slice()" in result.output
        assert "out of range" in result.output


def test_empty_brackets_are_not_a_slice():
    result = run_echo("say([1, 2][]);\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "Syntax Error" in result.output


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
    say(xs[1:]);
    say(xs[:2]);
    say(xs[:]);
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
    assert "xs[1:]" in formatted
    assert "xs[:2]" in formatted
    assert "xs[:]" in formatted
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


def test_flatmap_named_fn_and_lambda_flatten_one_level():
    result = run_echo(
        """
fn wrap(x: int) -> list {
    return [x, x];
}
fn nest(xs: list) -> list {
    return xs;
}
say(flatMap([1, 2], wrap));
say(flatMap([[1, 2], [3], []], nest));
say(flatMap([1, 2], fn(x: int) -> list { return [[x]]; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 1, 2, 2]", "[1, 2, 3]", "[[1], [2]]"]


def test_flatmap_empty_list():
    result = run_echo(
        """
fn boom(x: int) -> list {
    return fail("called");
}
empty: list = [];
say(flatMap(empty, boom));
say(flatMap(empty, fn(x: int) -> list { return fail("called"); }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[]"]


def test_flatmap_do_not_mutate_input():
    result = run_echo(
        """
nums: list = [1, 2, 3];
flat: list = nums.flatMap(fn(x: int) -> list { return [x]; });
say(nums);
say(flat);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[1, 2, 3]"]


def test_flatmap_method_and_keyword_form():
    result = run_echo(
        """
fn wrap(x: int) -> list {
    return [x, x * 10];
}
nums: list = [1, 2];
say(nums.flatMap(wrap));
say(flatMap(items: nums, f: wrap));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 10, 2, 20]", "[1, 10, 2, 20]"]


def test_flatmap_callback_must_return_list():
    result = run_echo(
        """
say(flatMap([1, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "flatMap()" in result.output
    assert "list" in result.output
    assert "E2839" in result.output


def test_flatmap_wrong_callback_type():
    not_fn = run_echo("say(flatMap([1, 2], 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "flatMap()" in not_fn.output
    assert "function" in not_fn.output
    assert "E2837" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> list {
    return [a, b];
}
say(flatMap([1, 2], add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "flatMap()" in wrong_arity.output
    assert "one argument" in wrong_arity.output
    assert "E2838" in wrong_arity.output

    extra_default = run_echo(
        """
fn wrap(x: int, extra: int = 0) -> list {
    return [x];
}
say(flatMap([1, 2], wrap));
"""
    )
    assert extra_default.exit_code == 1
    assert_no_python_leak(extra_default)
    assert "one argument" in extra_default.output
    assert "E2838" in extra_default.output


def test_flatmap_callback_abort():
    result = run_echo(
        """
say(flatMap([1, 2, 3], fn(x: int) -> list { return fail("flattened"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "flattened" in result.output


def test_some_every_findindex_named_fn_and_lambda():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}
fn odd(x: int) -> bool {
    return x % 2 == 1;
}
nums: list = [1, 2, 3, 4];
say(some(nums, even));
say(some(nums, fn(x: int) -> bool { return x > 10; }));
say(every(nums, odd));
say(every(nums, fn(x: int) -> bool { return x > 0; }));
say(findIndex(nums, even));
say(findIndex(nums, fn(x: int) -> bool { return x == 3; }));
say(find(nums, 3));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "false", "false", "true", "1", "2", "2"]


def test_some_every_findindex_empty_list():
    result = run_echo(
        """
fn boom(x: int) -> bool {
    return fail("called");
}
empty: list = [];
say(some(empty, boom));
say(every(empty, boom));
say(findIndex(empty, boom));
say(some(empty, fn(x: int) -> bool { return fail("called"); }));
say(every(empty, fn(x: int) -> bool { return fail("called"); }));
say(findIndex(empty, fn(x: int) -> bool { return fail("called"); }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["false", "true", "-1", "false", "true", "-1"]


def test_some_every_findindex_short_circuit():
    some_hit = run_echo(
        """
say(some([1, 2, 3], fn(x: int) -> bool {
    if x == 1 {
        return true;
    }
    return fail("some continued");
}));
"""
    )
    assert some_hit.exit_code == 0
    assert some_hit.lines == ["true"]

    every_miss = run_echo(
        """
say(every([1, 2, 3], fn(x: int) -> bool {
    if x == 1 {
        return false;
    }
    return fail("every continued");
}));
"""
    )
    assert every_miss.exit_code == 0
    assert every_miss.lines == ["false"]

    find_hit = run_echo(
        """
say(findIndex([1, 2, 3], fn(x: int) -> bool {
    if x == 1 {
        return true;
    }
    return fail("findIndex continued");
}));
"""
    )
    assert find_hit.exit_code == 0
    assert find_hit.lines == ["0"]


def test_some_every_findindex_do_not_mutate_input():
    result = run_echo(
        """
nums: list = [1, 2, 3];
has_even: bool = nums.some(fn(x: int) -> bool { return x % 2 == 0; });
all_positive: bool = nums.every(fn(x: int) -> bool { return x > 0; });
idx: int = nums.findIndex(fn(x: int) -> bool { return x == 2; });
say(nums);
say(has_even);
say(all_positive);
say(idx);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "true", "true", "1"]


def test_some_every_findindex_method_and_keyword_form():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}
fn positive(x: int) -> bool {
    return x > 0;
}
nums: list = [1, 2, 3];
say(nums.some(even));
say(some(items: nums, f: even));
say(nums.every(positive));
say(every(items: nums, f: positive));
say(nums.findIndex(even));
say(findIndex(items: nums, f: even));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["true", "true", "true", "true", "1", "1"]


def test_some_every_findindex_requires_bool_not_int():
    some_int = run_echo(
        """
say(some([1, 0, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert some_int.exit_code == 1
    assert_no_python_leak(some_int)
    assert "some()" in some_int.output
    assert "bool" in some_int.output
    assert "E2831" in some_int.output

    every_int = run_echo(
        """
say(every([1, 0, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert every_int.exit_code == 1
    assert_no_python_leak(every_int)
    assert "every()" in every_int.output
    assert "bool" in every_int.output
    assert "E2831" in every_int.output

    find_int = run_echo(
        """
say(findIndex([1, 0, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert find_int.exit_code == 1
    assert_no_python_leak(find_int)
    assert "findIndex()" in find_int.output
    assert "bool" in find_int.output
    assert "E2831" in find_int.output


def test_some_every_findindex_wrong_callback_type():
    not_fn = run_echo("say(some([1, 2], 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "some()" in not_fn.output
    assert "function" in not_fn.output
    assert "E2840" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> bool {
    return a == b;
}
say(every([1, 2], add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "every()" in wrong_arity.output
    assert "one argument" in wrong_arity.output
    assert "E2841" in wrong_arity.output

    extra_default = run_echo(
        """
fn even(x: int, extra: int = 0) -> bool {
    return x % 2 == 0;
}
say(findIndex([1, 2], even));
"""
    )
    assert extra_default.exit_code == 1
    assert_no_python_leak(extra_default)
    assert "one argument" in extra_default.output
    assert "E2841" in extra_default.output


def test_some_every_findindex_callback_abort():
    some_abort = run_echo(
        """
say(some([1, 2, 3], fn(x: int) -> bool { return fail("some aborted"); }));
"""
    )
    assert some_abort.exit_code == 1
    assert_no_python_leak(some_abort)
    assert "some aborted" in some_abort.output

    every_abort = run_echo(
        """
say(every([1, 2, 3], fn(x: int) -> bool { return fail("every aborted"); }));
"""
    )
    assert every_abort.exit_code == 1
    assert_no_python_leak(every_abort)
    assert "every aborted" in every_abort.output

    find_abort = run_echo(
        """
say(findIndex([1, 2, 3], fn(x: int) -> bool { return fail("findIndex aborted"); }));
"""
    )
    assert find_abort.exit_code == 1
    assert_no_python_leak(find_abort)
    assert "findIndex aborted" in find_abort.output


def test_zip_equal_and_unequal_lengths():
    result = run_echo(
        """
say(zip([1, 2], [10, 20]));
say(zip([1, 2, 3], [10, 20]));
say(zip([1], [10, 20, 30]));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[1, 10], [2, 20]]", "[[1, 10], [2, 20]]", "[[1, 10]]"]


def test_zip_empty_either_side():
    result = run_echo(
        """
empty: list = [];
say(zip(empty, [1, 2]));
say(zip([1, 2], empty));
say(zip(empty, empty));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[]", "[]"]


def test_zip_does_not_mutate_input():
    result = run_echo(
        """
left: list = [1, 2];
right: list = [10, 20];
paired: list = zip(left, right);
paired.push([9, 9]);
say(left);
say(right);
say(paired);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2]", "[10, 20]", "[[1, 10], [2, 20], [9, 9]]"]


def test_zip_method_and_keyword_form():
    result = run_echo(
        """
left: list = [1, 2];
right: list = [10, 20];
say(left.zip(right));
say(zip(left: left, right: right));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[1, 10], [2, 20]]", "[[1, 10], [2, 20]]"]


def test_zip_rejects_non_list():
    left = run_echo("say(zip(1, [1]));\n")
    assert left.exit_code == 1
    assert_no_python_leak(left)
    assert "zip()" in left.output
    assert "list" in left.output

    right = run_echo('say(zip([1], "x"));\n')
    assert right.exit_code == 1
    assert_no_python_leak(right)
    assert "zip()" in right.output
    assert "list" in right.output


def test_unique_first_occurrences_in_order():
    result = run_echo(
        """
say(unique([1, 2, 1, 3, 2]));
say(unique([true, 1, true, 1]));
say(unique(["a", "b", "a"]));
say(unique([[true], [1], [true]]));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[true, 1]", '["a", "b"]', "[[true], [1]]"]


def test_unique_empty_and_no_mutate():
    result = run_echo(
        """
empty: list = [];
say(unique(empty));
nums: list = [1, 1, 2];
out: list = nums.unique();
out.push(9);
say(nums);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[1, 1, 2]", "[1, 2, 9]"]


def test_unique_method_and_keyword_form():
    result = run_echo(
        """
nums: list = [2, 2, 3];
say(nums.unique());
say(unique(items: nums));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[2, 3]", "[2, 3]"]


def test_unique_rejects_non_list():
    number = run_echo("say(unique(1));\n")
    assert number.exit_code == 1
    assert_no_python_leak(number)
    assert "unique()" in number.output
    assert "list" in number.output

    text = run_echo('say("ab".unique());\n')
    assert text.exit_code == 1
    assert_no_python_leak(text)
    assert "unique()" in text.output
    assert "list" in text.output


def test_chunk_even_and_short_last():
    result = run_echo(
        """
say(chunk([1, 2, 3, 4], 2));
say(chunk([1, 2, 3, 4, 5], 2));
say(chunk([1, 2, 3], 5));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[1, 2], [3, 4]]", "[[1, 2], [3, 4], [5]]", "[[1, 2, 3]]"]


def test_chunk_empty_and_no_mutate():
    result = run_echo(
        """
empty: list = [];
say(chunk(empty, 2));
nums: list = [1, 2, 3];
out: list = nums.chunk(2);
out[0][0] = 9;
say(nums);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[1, 2, 3]", "[[9, 2], [3]]"]


def test_chunk_method_and_keyword_form():
    result = run_echo(
        """
nums: list = [1, 2, 3, 4];
say(nums.chunk(3));
say(chunk(items: nums, size: 3));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[1, 2, 3], [4]]", "[[1, 2, 3], [4]]"]


def test_chunk_size_must_be_int_at_least_one():
    zero = run_echo("say(chunk([1, 2], 0));\n")
    assert zero.exit_code == 1
    assert_no_python_leak(zero)
    assert "E2842" in zero.output

    negative = run_echo("say(chunk([1, 2], -1));\n")
    assert negative.exit_code == 1
    assert_no_python_leak(negative)
    assert "E2842" in negative.output

    flag = run_echo("say(chunk([1, 2], true));\n")
    assert flag.exit_code == 1
    assert_no_python_leak(flag)
    assert "E2842" in flag.output

    number = run_echo("say(chunk(1, 2));\n")
    assert number.exit_code == 1
    assert_no_python_leak(number)
    assert "chunk()" in number.output
    assert "list" in number.output


def test_range_list_exclusive_matches_dots():
    result = run_echo(
        """
say(rangeList(0, 5));
say(rangeList(0, 0));
say(rangeList(5, 3));
say(rangeList(-2, 2));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[0, 1, 2, 3, 4]", "[]", "[]", "[-2, -1, 0, 1]"]


def test_range_list_inclusive_matches_dot_dot():
    result = run_echo(
        """
say(rangeListInclusive(0, 5));
say(rangeListInclusive(0, 0));
say(rangeListInclusive(5, 3));
say(rangeListInclusive(-2, 2));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[0, 1, 2, 3, 4, 5]", "[0]", "[]", "[-2, -1, 0, 1, 2]"]


def test_range_list_keyword_form():
    result = run_echo(
        """
say(rangeList(start: 1, end: 4));
say(rangeListInclusive(start: 1, end: 4));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[1, 2, 3, 4]"]


def test_range_list_rejects_non_int_bounds():
    flag = run_echo("say(rangeList(true, 3));\n")
    assert flag.exit_code == 1
    assert_no_python_leak(flag)
    assert "E2843" in flag.output

    text = run_echo('say(rangeListInclusive("a", 3));\n')
    assert text.exit_code == 1
    assert_no_python_leak(text)
    assert "E2843" in text.output


def test_map_values_named_fn_and_lambda():
    result = run_echo(
        """
fn double(x: int) -> int {
    return x * 2;
}

scores: hash = { a: 1, b: 2 };
say(mapValues(scores, double));
say(mapValues(scores, fn(x: int) -> int { return x + 1; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ['{"a": 2, "b": 4}', '{"a": 2, "b": 3}']


def test_map_values_empty_and_no_mutate():
    result = run_echo(
        """
empty: hash = {};
say(mapValues(empty, fn(x: int) -> int { return x; }));
scores: hash = { a: 1, b: 2 };
out: hash = scores.mapValues(fn(x: int) -> int { return x * 10; });
say(scores);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["{}", '{"a": 1, "b": 2}', '{"a": 10, "b": 20}']


def test_map_values_method_and_keyword_form():
    result = run_echo(
        """
fn triple(x: int) -> int {
    return x * 3;
}

scores: hash = { a: 1 };
say(scores.mapValues(triple));
say(mapValues(items: scores, f: triple));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ['{"a": 3}', '{"a": 3}']


def test_map_values_wrong_callback():
    not_fn = run_echo("say(mapValues({ a: 1 }, 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "E2844" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> int {
    return a + b;
}
say(mapValues({ a: 1 }, add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "E2845" in wrong_arity.output

    number = run_echo("say(mapValues(1, fn(x: int) -> int { return x; }));\n")
    assert number.exit_code == 1
    assert_no_python_leak(number)
    assert "mapValues()" in number.output
    assert "hash" in number.output


def test_map_values_callback_abort():
    result = run_echo(
        """
say(mapValues({ a: 1, b: 2 }, fn(x: int) -> int { return fail("mapped"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "mapped" in result.output


def test_hash_filter_keeps_bool_true():
    result = run_echo(
        """
fn positive(x: int) -> bool {
    return x > 0;
}

scores: hash = { a: -1, b: 2, c: 0 };
say(filter(scores, positive));
say(filter(scores, fn(x: int) -> bool { return x == 0; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ['{"b": 2}', '{"c": 0}']


def test_hash_filter_empty_and_no_mutate():
    result = run_echo(
        """
empty: hash = {};
say(filter(empty, fn(x: int) -> bool { return true; }));
scores: hash = { a: 1, b: 2 };
out: hash = scores.filter(fn(x: int) -> bool { return x > 1; });
say(scores);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["{}", '{"a": 1, "b": 2}', '{"b": 2}']


def test_hash_filter_method_and_keyword_and_list_still_works():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}

scores: hash = { a: 1, b: 2 };
nums: list = [1, 2, 3, 4];
say(scores.filter(even));
say(filter(items: scores, f: even));
say(filter(nums, even));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ['{"b": 2}', '{"b": 2}', "[2, 4]"]


def test_hash_filter_requires_bool_not_int():
    result = run_echo("say(filter({ a: 1, b: 0 }, fn(x: int) -> int { return x; }));\n")
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2831" in result.output
    assert "filter()" in result.output


def test_hash_filter_callback_abort():
    result = run_echo(
        """
say(filter({ a: 1, b: 2 }, fn(x: int) -> bool { return fail("filtered"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "filtered" in result.output


def test_function_type_trailing_defaults_assign_and_call():
    result = run_echo(
        """
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
full: fn(int, int) -> int = add;
narrow: fn(int) -> int = add;
say(full(2, 3));
say(narrow(2));
say(add(2));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["5", "2", "2"]


def test_function_type_lambda_trailing_defaults():
    result = run_echo(
        """
narrow: fn(int) -> int = fn(x: int, y: int = 1) -> int { return x + y; };
full: fn(int, int) -> int = fn(x: int, y: int = 1) -> int { return x * y; };
say(narrow(4));
say(full(4, 3));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["5", "12"]


def test_function_type_defaults_as_callback():
    result = run_echo(
        """
fn apply(cb: fn(int) -> int, x: int) -> int {
    return cb(x);
}
fn applyFull(cb: fn(int, int) -> int, x: int, y: int) -> int {
    return cb(x, y);
}
fn add(x: int, y: int = 10) -> int {
    return x + y;
}
say(apply(add, 5));
say(applyFull(add, 5, 2));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["15", "7"]


def test_function_type_cannot_drop_required_parameter():
    result = run_echo(
        """
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
tooNarrow: fn() -> int = add;
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "E2001" in result.output
    assert "fn() -> int" in result.output


def test_function_type_required_params_must_match():
    missing = run_echo(
        """
fn add(x: int, y: int) -> int {
    return x + y;
}
narrow: fn(int) -> int = add;
"""
    )
    assert missing.exit_code == 1
    assert_no_python_leak(missing)
    assert "E2001" in missing.output

    wrong_type = run_echo(
        """
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
asStr: fn(str) -> int = add;
"""
    )
    assert wrong_type.exit_code == 1
    assert_no_python_leak(wrong_type)
    assert "E2001" in wrong_type.output


def test_function_type_variadic_must_match():
    dropped = run_echo(
        """
fn total(x: int, rest: int...) -> int {
    return x;
}
narrow: fn(int) -> int = total;
"""
    )
    assert dropped.exit_code == 1
    assert_no_python_leak(dropped)
    assert "E2001" in dropped.output

    matched = run_echo(
        """
fn total(x: int, rest: int...) -> int {
    sum: int = x;
    foreach n: int in rest {
        sum = sum + n;
    }
    return sum;
}
op: fn(int, int...) -> int = total;
say(op(1, 2, 3));
"""
    )
    assert matched.exit_code == 0
    assert matched.output.strip() == "6"

    default_before_variadic = run_echo(
        """
fn total(x: int, y: int = 0, rest: int...) -> int {
    sum: int = x + y;
    foreach n: int in rest {
        sum = sum + n;
    }
    return sum;
}
narrow: fn(int, int...) -> int = total;
full: fn(int, int, int...) -> int = total;
say(narrow(1, 2, 3));
say(full(1, 4, 5));
"""
    )
    assert default_before_variadic.exit_code == 0
    assert default_before_variadic.lines == ["6", "10"]


def test_function_type_call_arity_follows_declared_type():
    extra = run_echo(
        """
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
narrow: fn(int) -> int = add;
say(narrow(1, 2));
"""
    )
    assert extra.exit_code == 1
    assert "Semantic Error" in extra.output
    assert "expected at most 1" in extra.output

    missing = run_echo(
        """
fn add(x: int, y: int = 0) -> int {
    return x + y;
}
full: fn(int, int) -> int = add;
say(full(1));
"""
    )
    assert missing.exit_code == 1
    assert "Semantic Error" in missing.output
    assert "expected 2" in missing.output


def test_flatten_one_level():
    result = run_echo(
        """
say(flatten([[1, 2], [3], []]));
say(flatten([[[1, 2]], [3]]));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[[1, 2], 3]"]


def test_flatten_empty_and_no_mutate():
    result = run_echo(
        """
empty: list = [];
say(flatten(empty));
nums: list = [[1], [2, 3]];
out: list = nums.flatten();
out.push(9);
say(nums);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[]", "[[1], [2, 3]]", "[1, 2, 3, 9]"]


def test_flatten_method_and_keyword_form():
    result = run_echo(
        """
nums: list = [[1, 2], [3]];
say(nums.flatten());
say(flatten(items: nums));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[1, 2, 3]", "[1, 2, 3]"]


def test_flatten_rejects_top_level_non_list():
    mixed = run_echo("say(flatten([1, [2]]));\n")
    assert mixed.exit_code == 1
    assert_no_python_leak(mixed)
    assert "E2846" in mixed.output
    assert "flatten()" in mixed.output

    number = run_echo("say(flatten(1));\n")
    assert number.exit_code == 1
    assert_no_python_leak(number)
    assert "flatten()" in number.output
    assert "list" in number.output


def test_partition_matches_and_rest():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}
say(partition([1, 2, 3, 4], even));
say(partition([1, 2, 3, 4], fn(x: int) -> bool { return x > 2; }));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[2, 4], [1, 3]]", "[[3, 4], [1, 2]]"]


def test_partition_empty_and_no_mutate():
    result = run_echo(
        """
empty: list = [];
say(partition(empty, fn(x: int) -> bool { return true; }));
nums: list = [1, 2, 3];
out: list = nums.partition(fn(x: int) -> bool { return x > 1; });
out[0].push(9);
say(nums);
say(out);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[], []]", "[1, 2, 3]", "[[2, 3, 9], [1]]"]


def test_partition_method_and_keyword_form():
    result = run_echo(
        """
fn even(x: int) -> bool {
    return x % 2 == 0;
}
nums: list = [1, 2, 3];
say(nums.partition(even));
say(partition(items: nums, f: even));
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["[[2], [1, 3]]", "[[2], [1, 3]]"]


def test_partition_requires_bool_not_int():
    result = run_echo(
        """
say(partition([1, 0, 2], fn(x: int) -> int { return x; }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "partition()" in result.output
    assert "bool" in result.output
    assert "E2831" in result.output


def test_partition_wrong_callback():
    not_fn = run_echo("say(partition([1, 2], 1));\n")
    assert not_fn.exit_code == 1
    assert_no_python_leak(not_fn)
    assert "partition()" in not_fn.output
    assert "function" in not_fn.output
    assert "E2847" in not_fn.output

    wrong_arity = run_echo(
        """
fn add(a: int, b: int) -> bool {
    return a == b;
}
say(partition([1, 2], add));
"""
    )
    assert wrong_arity.exit_code == 1
    assert_no_python_leak(wrong_arity)
    assert "partition()" in wrong_arity.output
    assert "one argument" in wrong_arity.output
    assert "E2848" in wrong_arity.output


def test_partition_callback_abort():
    result = run_echo(
        """
say(partition([1, 2], fn(x: int) -> bool { return fail("split"); }));
"""
    )
    assert result.exit_code == 1
    assert_no_python_leak(result)
    assert "split" in result.output



