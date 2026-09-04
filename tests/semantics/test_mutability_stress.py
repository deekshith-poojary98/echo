from helpers import run_echo


def test_multiple_closures_mutate_the_same_captured_variable():
    result = run_echo(
        """
fn outer() {
    n: int = 0;
    fn addOne() {
        use mut n;
        n = n + 1;
    }
    fn addTen() {
        use mut n;
        n = n + 10;
    }
    addOne();
    addTen();
    say(n);
}
outer();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "11"


def test_nested_closure_mutation_requires_use_mut_on_the_inner_function():
    result = run_echo(
        """
fn outer() {
    n: int = 0;
    fn mid() {
        use mut n;
        fn inner() {
            n = n + 1;
        }
        inner();
    }
    mid();
}
outer();
"""
    )
    assert result.exit_code == 1
    assert "outer variable 'n'" in result.output


def test_deeply_nested_use_mut_can_mutate_captured_local():
    result = run_echo(
        """
fn outer() {
    n: int = 0;
    fn mid() {
        fn inner() {
            use mut n;
            n = n + 1;
        }
        inner();
    }
    mid();
    say(n);
}
outer();
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_use_mut_applies_inside_loop_blocks():
    result = run_echo(
        """
count: int = 0;
fn bump() {
    use mut count;
    for i: int in 1..3 {
        count = count + 1;
    }
}
bump();
say(count);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_readonly_use_forbids_assignment():
    result = run_echo(
        """
count: int = 0;
fn bump() {
    use count;
    count = count + 1;
}
bump();
"""
    )
    assert result.exit_code == 1
    assert "without 'use mut'" in result.output


def test_use_outside_function_is_semantic():
    result = run_echo("use mut x;\n")
    assert result.exit_code == 1
    assert "Semantic Error" in result.output
    assert "inside functions" in result.output


def test_use_undefined_name_is_semantic():
    result = run_echo(
        """
fn bump() {
    use mut missing;
}
bump();
"""
    )
    assert result.exit_code == 1
    assert "undefined" in result.output


def test_duplicate_use_in_one_function_is_an_error():
    result = run_echo(
        """
count: int = 0;
fn bump() {
    use mut count;
    use mut count;
    count = count + 1;
}
bump();
"""
    )
    assert result.exit_code == 1
    assert "already imported" in result.output


def test_shadowing_local_does_not_write_through_outer_even_with_use_mut():
    result = run_echo(
        """
x: int = 1;
fn f() {
    use mut x;
    x: int = 2;
    x = 3;
}
f();
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "1"


def test_compound_assignment_of_outer_name_requires_use_mut():
    result = run_echo(
        """
n: int = 1;
fn bump() {
    n += 1;
}
bump();
"""
    )
    assert result.exit_code == 1
    assert "without 'use mut'" in result.output


def test_compound_assignment_with_use_mut():
    result = run_echo(
        """
n: int = 1;
fn bump() {
    use mut n;
    n += 2;
}
bump();
say(n);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_list_push_on_outer_name_requires_use_mut():
    result = run_echo(
        """
items: list = [];
fn add() {
    items.push(1);
}
add();
"""
    )
    assert result.exit_code == 1
    assert "without 'use mut'" in result.output


def test_list_push_with_use_mut_mutates_shared_list():
    result = run_echo(
        """
items: list = [];
fn add() {
    use mut items;
    items.push(1);
}
add();
add();
say(items);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 1]"


def test_index_assignment_on_outer_name_requires_use_mut():
    result = run_echo(
        """
items: list = [0];
fn set() {
    items[0] = 9;
}
set();
"""
    )
    assert result.exit_code == 1
    assert "without 'use mut'" in result.output


def test_index_assignment_with_use_mut():
    result = run_echo(
        """
items: list = [0];
fn set() {
    use mut items;
    items[0] = 9;
}
set();
say(items);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[9]"


def test_rebinding_parameter_does_not_rebind_caller():
    result = run_echo(
        """
fn replace(n: int) {
    n = 99;
    say(n);
}
x: int = 1;
replace(x);
say(x);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["99", "1"]


def test_mutating_list_parameter_mutates_caller_collection():
    result = run_echo(
        """
fn add(items: list) {
    items.push(3);
}
nums: list = [1, 2];
add(nums);
say(nums);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "[1, 2, 3]"
