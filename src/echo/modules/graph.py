from __future__ import annotations

from pathlib import Path


from echo.errors import ModuleGraphError


class ModuleGraph:
    def __init__(self) -> None:
        self._nodes: dict[Path, None] = {}
        self._edges: dict[Path, set[Path]] = {}

    def canonicalize(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()

    def add_module(self, path: str | Path) -> Path:
        identity = self.canonicalize(path)
        if identity not in self._nodes:
            self._nodes[identity] = None
            self._edges[identity] = set()
        return identity

    def add_dependency(self, importer: str | Path, dependency: str | Path) -> None:
        src = self.add_module(importer)
        dst = self.add_module(dependency)
        self._edges[src].add(dst)

    def modules(self) -> list[Path]:
        return list(self._nodes)

    def dependencies_of(self, path: str | Path) -> frozenset[Path]:
        identity = self.canonicalize(path)
        return frozenset(self._edges.get(identity, ()))

    def detect_cycles(self) -> None:
        visiting: set[Path] = set()
        visited: set[Path] = set()
        stack: list[Path] = []

        def visit(node: Path) -> None:
            if node in visited:
                return
            if node in visiting:
                cycle_start = stack.index(node)
                cycle = stack[cycle_start:] + [node]
                names = " -> ".join(part.name for part in cycle)
                raise ModuleGraphError(
                    f"circular dependency: {names}",
                    code="E3003",
                )
            visiting.add(node)
            stack.append(node)
            for dependency in self._edges[node]:
                visit(dependency)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for node in self._nodes:
            visit(node)

    def dependency_order(self, entry: str | Path | None = None) -> list[Path]:
        self.detect_cycles()
        if entry is None:
            roots = list(self._nodes)
        else:
            roots = [self.canonicalize(entry)]
            if roots[0] not in self._nodes:
                raise ModuleGraphError(
                    f"module '{roots[0].name}' is not in the graph",
                    code="E3004",
                )

        ordered: list[Path] = []
        seen: set[Path] = set()

        def visit(node: Path) -> None:
            if node in seen:
                return
            seen.add(node)
            for dependency in self._edges[node]:
                visit(dependency)
            ordered.append(node)

        for root in roots:
            visit(root)
        return ordered
