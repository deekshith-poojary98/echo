from pathlib import Path
import argparse
import re
import sys

from echo_lexer import Lexer
from echo_parser import Parser
from echo_interpreter import Interpreter, set_rich_warnings_enabled

try:
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    Console = None
    Panel = None


def _resolve_source_path(source_path: str) -> Path:
    return Path(source_path).expanduser().resolve()


def _use_rich(plain: bool) -> bool:
    return (not plain) and Console is not None and Panel is not None


def _print_error(title: str, message: str, plain: bool) -> None:
    if _use_rich(plain):
        console = Console()
        panel = Panel(message, title=title, border_style="red", expand=False)
        console.print(panel)
        return

    print(f"{title}: {message}")


def _print_hint(hint: str, plain: bool) -> None:
    if _use_rich(plain):
        console = Console()
        panel = Panel(hint, title="Hint", border_style="cyan", expand=False)
        console.print(panel)
        return

    print(hint)


def _build_hint(message: str) -> str | None:
    if "Expected PUNCTUATION ;" in message:
        return "Hint: You may be missing a semicolon ';' at the end of the previous statement."

    if "Expected PUNCTUATION :" in message and "KEYWORD(in" in message:
        return "Hint: Loop variables must include a type, e.g. 'foreach item: dynamic in items { ... }' or 'for i: int in 0..10 { ... }'."

    if "Expected PUNCTUATION {" in message:
        return "Hint: A block opening '{' is missing. Check function, if/else, while, for, or foreach headers."

    if "Variable '" in message and "is not declared" in message:
        return "Hint: Declare variables with a type before assigning, e.g. 'name: str = \"Echo\";'."

    if "Variable '" in message and "is not defined" in message:
        return "Hint: Check for typos and scope. If inside a function, use 'use var_name;' or 'use mut var_name;' for outer-scope variables."

    if "missing a closing ')'" in message:
        return "Hint: You opened a function call with '(' but never closed it. Make sure every '(' has a matching ')'."

    if "missing a closing ']'" in message:
        return "Hint: You opened a list with '[' but never closed it. Make sure every '[' has a matching ']'."

    if "missing a closing '}'" in message:
        return "Hint: You opened a hash with '{' but never closed it. Make sure every '{' has a matching '}'."

    if "not defined" in message and "Function" in message:
        return "Hint: Check that the function is defined with 'fn name(...) { ... }' before calling it."

    if "Cannot modify immutable import" in message:
        return "Hint: Use 'use mut variable_name;' inside the function before mutating that imported variable."

    if "return' statement outside function" in message:
        return "Hint: 'return' can only be used inside a function body."

    if "break' statement outside loop" in message or "continue' statement outside loop" in message:
        return "Hint: 'break' and 'continue' can only be used inside for/foreach/while loops."

    if re.search(r"Expected\s+\w+", message):
        return "Hint: Check the token shown after 'Expected ...'. The parser usually reports where structure first became invalid."

    return None


def _friendly_syntax_message(message: str) -> str:
    pattern = re.compile(
        r"Expected\s+(?P<expected_type>\w+)\s+(?P<expected_value>.+?),\s+got\s+"
        r"(?P<got_type>\w+)\((?P<got_payload>.*?)\)\s+at\s+line\s+(?P<line>\d+),\s+column\s+(?P<col>\d+)"
    )
    match = pattern.search(message)
    if not match:
        return message

    expected_type = match.group("expected_type")
    expected_value = match.group("expected_value").strip()
    got_payload = match.group("got_payload")
    line = match.group("line")
    col = match.group("col")

    got_value = got_payload.split(", line=")[0].strip()

    if expected_type == "PUNCTUATION" and expected_value == ";":
        return f"Line {line}, column {col}: I expected ';' before '{got_value}'."

    if expected_type == "PUNCTUATION" and expected_value == ":":
        return f"Line {line}, column {col}: I expected ':' before '{got_value}'."

    if expected_type == "PUNCTUATION" and expected_value == "{":
        return f"Line {line}, column {col}: I expected '{{' to start a code block before '{got_value}'."

    expected_text = expected_value if expected_value != "None" else expected_type.lower()
    return f"Line {line}, column {col}: I expected {expected_text} before '{got_value}'."


def run_file(source_path: str, plain: bool = False) -> int:
    file_path = _resolve_source_path(source_path)
    if not file_path.exists() or not file_path.is_file():
        _print_error("Error", f"source file not found: {file_path}", plain)
        return 1

    lex_obj = Lexer()
    parser_obj = None

    try:
        tokens = lex_obj.read_source(str(file_path))
        parser_obj = Parser(tokens)
        ast = parser_obj.parse()
        set_rich_warnings_enabled(not plain)
        interpreter = Interpreter()
        interpreter.execute(ast)
        return 0
    except SyntaxError as exc:
        message = str(exc)
        _print_error("Syntax Error", _friendly_syntax_message(message), plain)
        hint = _build_hint(message)
        if hint:
            _print_hint(hint, plain)
        return 1
    except NameError as exc:
        message = str(exc)
        _print_error("Name Error", message, plain)
        hint = _build_hint(message)
        if hint:
            _print_hint(hint, plain)
        return 1
    except TypeError as exc:
        message = str(exc)
        _print_error("Type Error", message, plain)
        hint = _build_hint(message)
        if hint:
            _print_hint(hint, plain)
        return 1
    except (ValueError, KeyError, IndexError, RuntimeError) as exc:
        message = str(exc)
        _print_error("Execution Error", message, plain)
        hint = _build_hint(message)
        if hint:
            _print_hint(hint, plain)
        return 1
    except Exception as exc:
        message = str(exc)
        _print_error("Execution Error", message, plain)
        hint = _build_hint(message)
        if hint:
            _print_hint(hint, plain)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an Echo source file")
    parser.add_argument("source", help="Path to .echo source file")
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable Rich styling and use plain text output",
    )
    args = parser.parse_args(argv)
    return run_file(args.source, plain=args.plain)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
