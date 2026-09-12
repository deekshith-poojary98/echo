from __future__ import annotations

from echo.errors import MutationError, SourceLocation

_frozen: dict[int, object] = {}


def freeze(value: object) -> None:
    """Mark a list or hash as frozen. Other values are already immutable."""
    if isinstance(value, (list, dict)):
        _frozen[id(value)] = value


def is_frozen(value: object) -> bool:
    return _frozen.get(id(value)) is value


def require_unfrozen(value: object, location: SourceLocation | None = None) -> None:
    if not is_frozen(value):
        return
    if isinstance(value, list):
        kind = "list"
    elif isinstance(value, dict):
        kind = "hash"
    else:
        kind = "value"
    raise MutationError(
        f"Cannot mutate frozen {kind}",
        location,
        help_text="This collection was bound with const. Reading, iterating, and helpers that return a new value are allowed.",
        code="E3203",
    )
