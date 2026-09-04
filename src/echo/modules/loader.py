from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from echo.errors import EchoError, ModuleLoadError
from echo.frontend.ast.nodes import ImportDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.modules.graph import ModuleGraph
from echo.modules.records import FAILED, INITIALIZED, INITIALIZING, Module
from echo.modules.resolver import ModuleResolver
from echo.runtime.context import Environment
from echo.runtime.functions import EchoFunction
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer
from echo.semantics.modules import ModuleSymbols


class ModuleLoader:
    def __init__(self, resolver: ModuleResolver | None = None) -> None:
        self._resolver = resolver or ModuleResolver()
        self._modules: dict[Path, Module] = {}
        self._declared_imports: dict[Path, list[str]] = {}
        self._initialized: list[Path] = []

    def declare_imports(self, importer_path: str | Path, names: Sequence[str]) -> None:
        identity = self._resolver.canonicalize(importer_path)
        self._declared_imports[identity] = list(names)

    def module(self, path: str | Path) -> Module | None:
        return self._modules.get(self._resolver.canonicalize(path))

    def modules(self) -> list[Module]:
        return list(self._modules.values())

    def initialized_paths(self) -> list[Path]:
        return list(self._initialized)

    def load(self, entry_path: str | Path) -> Module:
        entry = self._resolver.canonicalize(entry_path)
        graph = ModuleGraph()
        self._collect(entry, graph, set())
        graph.detect_cycles()
        self._analyze_modules()
        interpreter = Interpreter()
        for path in graph.dependency_order(entry):
            self._initialize(self._modules[path], interpreter)
        return self._modules[entry]

    def _collect(self, path: Path, graph: ModuleGraph, walked: set[Path]) -> Module:
        module = self._materialize(path)
        graph.add_module(module.path)
        if module.path in walked:
            return module
        walked.add(module.path)
        if not module.discovered:
            self._discover_imports(module)
            module.discovered = True
        for name in self._import_names(module):
            dependency = module.specifiers.get(name) or self._resolver.resolve(module.path, name)
            if dependency not in module.dependencies:
                module.dependencies.append(dependency)
            module.specifiers.setdefault(name, dependency)
            graph.add_dependency(module.path, dependency)
            self._collect(dependency, graph, walked)
        return module

    def _discover_imports(self, module: Module) -> None:
        for statement in module.ast.statements:
            if not isinstance(statement, ImportDeclaration):
                continue
            dependency = self._resolver.resolve(module.path, statement.module)
            module.imported_bindings.append((statement.name, dependency))
            module.specifiers[statement.module] = dependency

    def _import_names(self, module: Module) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()
        for statement in module.ast.statements:
            if isinstance(statement, ImportDeclaration) and statement.module not in seen:
                seen.add(statement.module)
                names.append(statement.module)
        for name in self._declared_imports.get(module.path, ()):
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names

    def _materialize(self, path: Path) -> Module:
        identity = self._resolver.canonicalize(path)
        existing = self._modules.get(identity)
        if existing is not None:
            return existing
        source = identity.read_text(encoding="utf-8")
        tokens = Lexer().tokenize(source, filename=str(identity))
        program = Parser(tokens).parse()
        module = Module(path=identity, source=source, ast=program)
        self._modules[identity] = module
        return module

    def _analyze_modules(self) -> None:
        collected: dict[Path, ModuleSymbols] = {
            module.path: SemanticAnalyzer().collect_symbols(module.ast)
            for module in self._modules.values()
        }
        for module in self._modules.values():
            dependencies: dict[str, ModuleSymbols] = {}
            for statement in module.ast.statements:
                if not isinstance(statement, ImportDeclaration):
                    continue
                dependency = module.specifiers[statement.module]
                dependencies[statement.module] = collected[dependency]
            analyzer = SemanticAnalyzer()
            analyzer.analyze(module.ast, dependencies=dependencies)
            module.exports = set(analyzer.module_symbols.exports)

    def _initialize(self, module: Module, interpreter: Interpreter) -> None:
        if module.state == INITIALIZED:
            return
        if module.state == FAILED:
            raise ModuleLoadError(
                f"module '{module.path.name}' previously failed to initialize",
                code="E3005",
            )
        if module.state == INITIALIZING:
            raise ModuleLoadError(
                f"module '{module.path.name}' is not fully initialized",
                code="E3005",
            )
        module.state = INITIALIZING
        env = Environment()
        module.env = env
        try:
            self._bind_imports(module, env)
            interpreter.execute(module.ast, env)
        except EchoError:
            module.state = FAILED
            raise
        except Exception as exc:
            module.state = FAILED
            raise ModuleLoadError(
                f"module '{module.path.name}' failed to initialize",
                code="E3005",
            ) from exc
        module.state = INITIALIZED
        self._initialized.append(module.path)

    def _bind_imports(self, module: Module, env: Environment) -> None:
        for name, dependency_path in module.imported_bindings:
            dependency = self._modules[dependency_path]
            value = self._export_value(dependency, name)
            if isinstance(value, EchoFunction):
                env.define_function(name, value)
            env.define(name, value, mutable=False)

    def _export_value(self, module: Module, name: str) -> object:
        env = module.env
        if env is None:
            raise ModuleLoadError(
                f"module '{module.path.name}' is not fully initialized",
                code="E3005",
            )
        if name in env.values:
            return env.values[name]
        function = env.functions.get(name)
        if function is not None:
            return function
        raise ModuleLoadError(
            f"module '{module.path.name}' has no export '{name}'",
            code="E3005",
        )
