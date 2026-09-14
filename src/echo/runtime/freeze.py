from __future__ import annotations

from echo.errors import MutationError, SourceLocation
from echo.runtime.instances import ClassInstance

_frozen: dict[int, object] = {}


def freeze(value: object) -> None:
    """Mark a list, hash, or class instance as frozen. Other values are already immutable."""
    if isinstance(value, (list, dict)):
        _frozen[id(value)] = value
    elif isinstance(value, ClassInstance):
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
    elif isinstance(value, ClassInstance):
        kind = value.class_name
    else:
        kind = "value"
    raise MutationError(
        f"Cannot mutate frozen {kind}",
        location,
        help_text="This value was bound with const. Reading is allowed; in-place mutation is not.",
        code="E3203",
    )
