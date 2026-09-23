from helpers import run_echo
from echo.formatter import format_source


def test_property_get_set_and_compound():
    result = run_echo(
        """
class Counter {
    new {
        priv n: int = 0;
    }

    get count(this) -> int {
        return this.n;
    }

    set count(this, value: int) {
        this.n = value;
    }
}

c: Counter = Counter {};
c.count = 10;
say(c.count);
c.count += 2;
say(c.count);
"""
    )
    assert result.exit_code == 0
    assert result.lines == ["10", "12"]


def test_property_read_only():
    result = run_echo(
        """
class Box {
    new {
        priv n: int = 1;
    }

    get value(this) -> int {
        return this.n;
    }
}

b: Box = Box {};
say(b.value);
b.value = 2;
"""
    )
    assert result.exit_code != 0
    assert "read-only" in result.output or "E3217" in result.output


def test_property_write_only():
    result = run_echo(
        """
class Sink {
    new {
        priv n: int = 0;
    }

    set value(this, v: int) {
        this.n = v;
    }
}

s: Sink = Sink {};
s.value = 5;
say(s.value);
"""
    )
    assert result.exit_code != 0
    assert "write-only" in result.output or "E3217" in result.output


def test_priv_getter_inaccessible_outside():
    result = run_echo(
        """
class Counter {
    new {
        priv n: int = 3;
    }

    priv get count(this) -> int {
        return this.n;
    }

    fn show(this) {
        say(this.count);
    }
}

c: Counter = Counter {};
c.show();
say(c.count);
"""
    )
    assert result.exit_code != 0
    assert "private" in result.output.lower() or "E3215" in result.output


def test_property_conflicts_with_field():
    result = run_echo(
        """
class Bad {
    new {
        n: int;
    }

    get n(this) -> int {
        return 1;
    }
}
"""
    )
    assert result.exit_code != 0
    assert "conflict" in result.output.lower()


def test_formatter_prints_get_set():
    formatted = format_source(
        """
class Counter {
    new { priv n: int = 0; }
    get count(this) -> int { return this.n; }
    set count(this, value: int) { this.n = value; }
}
"""
    )
    assert "get count(this) -> int" in formatted
    assert "set count(this, value: int)" in formatted
    assert format_source(formatted) == formatted
