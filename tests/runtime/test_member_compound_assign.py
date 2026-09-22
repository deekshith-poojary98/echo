from tests.helpers import run_echo


def test_member_compound_assignment_on_class_field():
    result = run_echo(
        """
class Counter {
    new {
        n: int;
    }

    fn bump(this) {
        this.n += 1;
    }
}

c: Counter = Counter { n: 10 };
c.n -= 3;
c.n *= 2;
c.bump();
say(c.n);
"""
    )
    assert result.exit_code == 0
    assert result.output.strip() == "15"


def test_member_compound_assignment_const_instance_is_error():
    result = run_echo(
        """
class Point {
    new {
        x: int;
    }
}

const p: Point = Point { x: 1 };
p.x += 1;
"""
    )
    assert result.exit_code != 0


def test_member_compound_assignment_unknown_field_is_error():
    result = run_echo(
        """
class Point {
    new {
        x: int;
    }
}

p: Point = Point { x: 1 };
p.y += 1;
"""
    )
    assert result.exit_code != 0
