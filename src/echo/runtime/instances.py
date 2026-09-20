from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClassInstance:
    class_name: str
    fields: dict[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:
        from echo.runtime.values import stringify

        return stringify(self)
