from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from echo.errors import EchoError, EchoExit, ModuleLoadError, ModuleResolveError, SourceLocation
from echo.frontend.ast.nodes import ImportDeclaration
from echo.frontend.lexer import Lexer
from echo.frontend.parser import Parser
from echo.modules.graph import ModuleGraph
from echo.modules.records import FAILED, INITIALIZED, INITIALIZING, Module
from echo.modules.resolver import ModuleResolver
from echo.runtime.builtins import BUILTIN_NAMES, prelude_builtin_names
from echo.runtime.context import Environment
from echo.runtime.functions import EchoFunction
from echo.runtime.host import Host
from echo.runtime.interpreter import Interpreter
from echo.semantics.analyzer import SemanticAnalyzer
from echo.semantics.modules import ModuleSymbols


class ModuleLoader:
    def __init__(self, resolver: ModuleResolver | None = None) -> None:
        self.resolver = resolver or ModuleResolver()
        self._modules: dict[Path, Module] = {}
        self._declared_imports: dict[Path, list[str]] = {}
        self._initialized: list[Path] = []
        self.host = Host()

    def declare_imports(self, importer_path: str | Path, names: Sequence[str]) -> None:
        identity = self.resolver.canonicalize(importer_path)
        self._declared_imports[identity] = list(names)

    def module(self, path: str | Path) -> Module | None:
        return self._modules.get(self.resolver.canonicalize(path))

    def modules(self) -> list[Module]:
        return list(self._modules.values())

    def initialized_paths(self) -> list[Path]:
        return list(self._initialized)

    def load(
        self,
        entry_path: str | Path,
        host: Host | None = None,
        interpreter: Interpreter | None = None,
    ) -> Module:
        self.host = host or Host()
        entry = self.resolver.canonicalize(entry_path)
        graph = ModuleGraph()
        self._collect(entry, graph, set())
        graph.detect_cycles()
        self._analyze_modules()
        interpreter = interpreter or Interpreter(host=self.host)
        for path in graph.dependency_order(entry):
            self._initialize(self._modules[path], interpreter)
        return self._modules[entry]

    def check(self, entry_path: str | Path, host: Host | None = None) -> Module:
        self.host = host or self.host
        entry = self.resolver.canonicalize(entry_path)
        graph = ModuleGraph()
        self._collect(entry, graph, set())
        graph.detect_cycles()
        self._analyze_modules()
        return self._modules[entry]

    def _is_std_module(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.resolver.std_root)
            return True
        except ValueError:
            return False

    def _prelude_names_for(self, path: Path) -> frozenset[str]:
        if self._is_std_module(path):
            return BUILTIN_NAMES
        return prelude_builtin_names(require_std=self.host.require_std)

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
            dependency = module.specifiers.get(name) or self._resolve(module, name)
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
            dependency = self._resolve(module, statement.module, statement.location)
            module.imported_bindings.append((statement.name, dependency))
            module.specifiers[statement.module] = dependency

    def _resolve(
        self,
        module: Module,
        specifier: str,
        location: SourceLocation | None = None,
    ) -> Path:
        try:
            return self.resolver.resolve(module.path, specifier)
        except ModuleResolveError as exc:
            raise ModuleResolveError(
                exc.message,
                location=location if location is not None else exc.location,
                help_text=exc.help_text,
                code=exc.code,
            ) from None

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
        identity = self.resolver.canonicalize(path)
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
            scope = SemanticAnalyzer.module_scope(
                module.ast.location,
                names=self._prelude_names_for(module.path),
            )
            analyzer.analyze(module.ast, dependencies=dependencies, scope=scope)
            module.exports = set(analyzer.module_symbols.exports)
            module.class_exports = set(analyzer.module_symbols.classes) | set(
                analyzer.module_symbols.interfaces
            )

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
        previous = interpreter.prelude_names
        try:
            if self._is_std_module(module.path):
                interpreter.use_full_prelude()
            else:
                interpreter.use_host_prelude()
            self._bind_imports(module, env)
            interpreter.execute(module.ast, env)
        except EchoExit:
            raise
        except EchoError:
            module.state = FAILED
            raise
        except Exception as exc:
            module.state = FAILED
            raise ModuleLoadError(
                f"module '{module.path.name}' failed to initialize",
                code="E3005",
            ) from exc
        finally:
            interpreter.prelude_names = previous
        module.state = INITIALIZED
        self._initialized.append(module.path)

    def _bind_imports(self, module: Module, env: Environment) -> None:
        for name, dependency_path in module.imported_bindings:
            dependency = self._modules[dependency_path]
            if name in dependency.class_exports:
                record = dependency.env.resolve_class(name) if dependency.env is not None else None
                if record is not None:
                    env.define_class(name, record)
                continue
            value = self._export_value(dependency, name)
            if isinstance(value, EchoFunction):
                env.define_function(name, value)
            is_const = bool(dependency.env.const.get(name, False)) if dependency.env is not None else False
            env.define(name, value, mutable=False, const=is_const)

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
