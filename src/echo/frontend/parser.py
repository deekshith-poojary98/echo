from __future__ import annotations

from echo.errors import ParseError, SourceLocation
from echo.frontend.ast.nodes import (
    Argument,
    AssignmentStatement,
    BinaryExpression,
    BreakStatement,
    CallExpression,
    CompoundAssignment,
    ContinueStatement,
    ExportDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    ForeachStatement,
    FunctionDeclaration,
    HashLiteral,
    HashPair,
    IfStatement,
    ImportDeclaration,
    IndexAssignment,
    IndexExpression,
    ListLiteral,
    LiteralExpression,
    MemberExpression,
    ObjectType,
    Parameter,
    Program,
    ReturnStatement,
    Statement,
    StringInterpolation,
    StringLiteralExpression,
    TypeAliasStatement,
    TypeAnnotation,
    TypeName,
    UnaryExpression,
    UseStatement,
    VariableDeclaration,
    VariableExpression,
    WatchStatement,
    WhileStatement,
)
from echo.frontend.tokens import COMPOUND_OPS, Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements: list[Statement] = []
        location = self._location(self._peek())
        while not self._check(TokenType.EOF):
            statements.append(self.parse_statement())
        return Program(location, statements)

    def parse_statement(self) -> Statement:
        token = self._peek()
        if token.type == TokenType.IF:
            return self.parse_if()
        if token.type == TokenType.WHILE:
            return self.parse_while()
        if token.type == TokenType.FOR:
            return self.parse_for()
        if token.type == TokenType.FOREACH:
            return self.parse_foreach()
        if token.type == TokenType.FN:
            return self.parse_function()
        if token.type == TokenType.IMPORT:
            return self.parse_import()
        if token.type == TokenType.EXPORT:
            return self.parse_export()
        if token.type == TokenType.USE:
            return self.parse_use()
        if token.type == TokenType.WATCH:
            return self.parse_watch()
        if token.type == TokenType.TYPE_KW:
            if self._check_offset(1, TokenType.LEFT_PAREN):
                expr = self.parse_expression()
                self._expect(TokenType.SEMICOLON, ";")
                return ExpressionStatement(expr.location, expr)
            return self.parse_type_alias()
        if token.type == TokenType.RETURN:
            return self.parse_return()
        if token.type == TokenType.BREAK:
            return self.parse_break()
        if token.type == TokenType.CONTINUE:
            return self.parse_continue()
        return self.parse_assignment_or_expr()

    def parse_assignment_or_expr(self) -> Statement:
        if self._is_name(self._peek()) and self._check_offset(1, TokenType.COLON):
            name_token = self._advance()
            self._advance()
            declared_type = self._parse_type()
            if isinstance(declared_type, TypeName) and declared_type.name == "void":
                raise ParseError("Cannot use 'void' as a variable type", name_token.location)
            self._expect(TokenType.EQUAL, "=")
            value = self.parse_expression()
            self._expect(TokenType.SEMICOLON, ";")
            return VariableDeclaration(name_token.location, name_token.lexeme, declared_type, value)

        if self._is_name(self._peek()) and self._check_offset(1, TokenType.EQUAL):
            name_token = self._advance()
            self._advance()
            value = self.parse_expression()
            self._expect(TokenType.SEMICOLON, ";")
            return AssignmentStatement(name_token.location, name_token.lexeme, value)

        if self._is_name(self._peek()) and self._peek_offset(1) is not None and self._peek_offset(1).type in COMPOUND_OPS:
            name_token = self._advance()
            operator = self._advance()
            value = self.parse_expression()
            self._expect(TokenType.SEMICOLON, ";")
            return CompoundAssignment(name_token.location, name_token.lexeme, operator, value)

        if self._is_name(self._peek()) and self._check_offset(1, TokenType.LEFT_BRACKET):
            saved = self.pos
            name_token = self._advance()
            indices = []
            while self._match(TokenType.LEFT_BRACKET):
                indices.append(self.parse_expression())
                self._expect(TokenType.RIGHT_BRACKET, "]")
            if self._match(TokenType.EQUAL):
                value = self.parse_expression()
                self._expect(TokenType.SEMICOLON, ";")
                return IndexAssignment(name_token.location, name_token.lexeme, indices, value)
            self.pos = saved

        expr = self.parse_expression()
        self._expect(TokenType.SEMICOLON, ";")
        return ExpressionStatement(expr.location, expr)

    def parse_function(self) -> FunctionDeclaration:
        fn_token = self._expect(TokenType.FN, "fn")
        name = self._expect_name("function name")
        self._expect(TokenType.LEFT_PAREN, "(")
        parameters: list[Parameter] = []
        while not self._check(TokenType.RIGHT_PAREN) and not self._check(TokenType.EOF):
            param_token = self._expect_name_token("parameter name")
            self._expect(TokenType.COLON, ":")
            param_type = self._parse_type()
            parameters.append(Parameter(param_token.lexeme, param_type, param_token.location))
            self._match(TokenType.COMMA)
        self._expect(TokenType.RIGHT_PAREN, ")")

        return_type = None
        if self._match(TokenType.ARROW):
            return_type = self._parse_type()

        if self._match(TokenType.FAT_ARROW):
            body_expr = self.parse_expression()
            self._expect(TokenType.SEMICOLON, ";")
            return FunctionDeclaration(fn_token.location, name, parameters, body_expr, True, return_type)

        self._expect(TokenType.LEFT_BRACE, "{")
        body = self._parse_block_body()
        self._expect(TokenType.RIGHT_BRACE, "}")
        return FunctionDeclaration(fn_token.location, name, parameters, body, False, return_type)

    def parse_if(self) -> IfStatement:
        token = self._expect(TokenType.IF, "if")
        condition = self.parse_expression()
        self._expect(TokenType.LEFT_BRACE, "{")
        then_branch = self._parse_block_body()
        self._expect(TokenType.RIGHT_BRACE, "}")
        else_branch = None
        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                else_branch = [self.parse_if()]
            else:
                self._expect(TokenType.LEFT_BRACE, "{")
                else_branch = self._parse_block_body()
                self._expect(TokenType.RIGHT_BRACE, "}")
        return IfStatement(token.location, condition, then_branch, else_branch)

    def parse_while(self) -> WhileStatement:
        token = self._expect(TokenType.WHILE, "while")
        condition = self.parse_expression()
        self._expect(TokenType.LEFT_BRACE, "{")
        body = self._parse_block_body()
        self._expect(TokenType.RIGHT_BRACE, "}")
        return WhileStatement(token.location, condition, body)

    def parse_for(self) -> ForStatement:
        token = self._expect(TokenType.FOR, "for")
        var = self._expect_name("loop variable")
        self._expect(TokenType.COLON, ":")
        var_type = self._parse_type()
        self._expect(TokenType.IN, "in")
        start = self.parse_expression()
        range_token = self._peek()
        if range_token.type not in (TokenType.DOT_DOT, TokenType.DOT_DOT_DOT):
            raise ParseError("Expected '..' or '...' in for-range", range_token.location)
        inclusive = range_token.type == TokenType.DOT_DOT
        self._advance()
        end = self.parse_expression()
        if self._match(TokenType.BY):
            step = self.parse_expression()
        else:
            step = LiteralExpression(end.location, 1)
        self._expect(TokenType.LEFT_BRACE, "{")
        body = self._parse_block_body()
        self._expect(TokenType.RIGHT_BRACE, "}")
        return ForStatement(token.location, var, var_type, start, end, step, inclusive, body)

    def parse_foreach(self) -> ForeachStatement:
        token = self._expect(TokenType.FOREACH, "foreach")
        var = self._expect_name("loop variable")
        self._expect(TokenType.COLON, ":")
        var_type = self._parse_type()
        self._expect(TokenType.IN, "in")
        iterable = self.parse_expression()
        self._expect(TokenType.LEFT_BRACE, "{")
        body = self._parse_block_body()
        self._expect(TokenType.RIGHT_BRACE, "}")
        return ForeachStatement(token.location, var, var_type, iterable, body)

    def parse_return(self) -> ReturnStatement:
        token = self._expect(TokenType.RETURN, "return")
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self.parse_expression()
        self._expect(TokenType.SEMICOLON, ";")
        return ReturnStatement(token.location, value)

    def parse_break(self) -> BreakStatement:
        token = self._expect(TokenType.BREAK, "break")
        self._expect(TokenType.SEMICOLON, ";")
        return BreakStatement(token.location)

    def parse_continue(self) -> ContinueStatement:
        token = self._expect(TokenType.CONTINUE, "continue")
        self._expect(TokenType.SEMICOLON, ";")
        return ContinueStatement(token.location)

    def parse_import(self) -> ImportDeclaration:
        token = self._expect(TokenType.IMPORT, "import")
        name = self._expect_name("imported name")
        self._expect(TokenType.FROM, "from")
        module_token = self._peek()
        if module_token.type != TokenType.STRING:
            raise ParseError("Expected module name string", module_token.location)
        self._advance()
        if self._check(TokenType.INTERPOLATION_START):
            raise ParseError("Module name must be a plain string", self._peek().location)
        self._expect(TokenType.SEMICOLON, ";")
        return ImportDeclaration(token.location, name, module_token.lexeme)

    def parse_export(self) -> ExportDeclaration:
        token = self._expect(TokenType.EXPORT, "export")
        if self._check(TokenType.FN):
            declaration = self.parse_function()
            return ExportDeclaration(token.location, declaration.name, declaration)
        name_token = self._expect_name_token("exported name")
        if self._match(TokenType.COLON):
            declared_type = self._parse_type()
            if isinstance(declared_type, TypeName) and declared_type.name == "void":
                raise ParseError("Cannot use 'void' as a variable type", name_token.location)
            self._expect(TokenType.EQUAL, "=")
            value = self.parse_expression()
            self._expect(TokenType.SEMICOLON, ";")
            declaration = VariableDeclaration(name_token.location, name_token.lexeme, declared_type, value)
            return ExportDeclaration(token.location, name_token.lexeme, declaration)
        self._expect(TokenType.SEMICOLON, ";")
        return ExportDeclaration(token.location, name_token.lexeme)

    def parse_use(self) -> UseStatement:
        token = self._expect(TokenType.USE, "use")
        mutable = bool(self._match(TokenType.MUT))
        names = [self._expect_name("variable name")]
        while self._match(TokenType.COMMA):
            names.append(self._expect_name("variable name"))
        self._expect(TokenType.SEMICOLON, ";")
        return UseStatement(token.location, names, mutable)

    def parse_watch(self) -> WatchStatement:
        token = self._expect(TokenType.WATCH, "watch")
        names = [self._expect_name("variable name")]
        while self._match(TokenType.COMMA):
            names.append(self._expect_name("variable name"))
        self._expect(TokenType.SEMICOLON, ";")
        return WatchStatement(token.location, names)

    def parse_type_alias(self) -> TypeAliasStatement:
        token = self._expect(TokenType.TYPE_KW, "type")
        name_token = self._expect_name_token("type alias name")
        self._expect(TokenType.EQUAL, "=")
        target = self._parse_type()
        self._expect(TokenType.SEMICOLON, ";")
        if name_token.lexeme in {"int", "float", "str", "bool", "dynamic", "list", "hash", "void"}:
            raise ParseError(f"Cannot redefine built-in type '{name_token.lexeme}'", name_token.location)
        return TypeAliasStatement(token.location, name_token.lexeme, target)

    def parse_expression(self) -> Expression:
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        expr = self.parse_logical_and()
        while self._check(TokenType.OR_OR):
            operator = self._advance()
            right = self.parse_logical_and()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_logical_and(self) -> Expression:
        expr = self.parse_equality()
        while self._check(TokenType.AND_AND):
            operator = self._advance()
            right = self.parse_equality()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_equality(self) -> Expression:
        expr = self.parse_comparison()
        while self._check(TokenType.EQUAL_EQUAL) or self._check(TokenType.BANG_EQUAL):
            operator = self._advance()
            right = self.parse_comparison()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_comparison(self) -> Expression:
        expr = self.parse_term()
        while self._check(TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            operator = self._advance()
            right = self.parse_term()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_term(self) -> Expression:
        expr = self.parse_factor()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            operator = self._advance()
            right = self.parse_factor()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_factor(self) -> Expression:
        expr = self.parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self._advance()
            right = self.parse_unary()
            expr = BinaryExpression(expr.location, expr, operator, right)
        return expr

    def parse_unary(self) -> Expression:
        if self._check(TokenType.BANG, TokenType.MINUS):
            operator = self._advance()
            operand = self.parse_unary()
            return UnaryExpression(operator.location, operator, operand)
        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        expr = self.parse_primary()
        while True:
            if self._match(TokenType.DOT):
                name_token = self._expect_name_token("method or member name")
                if self._match(TokenType.LEFT_PAREN):
                    args = self._parse_arg_list(f"'{name_token.lexeme}()' call")
                    member = MemberExpression(expr.location, expr, name_token.lexeme)
                    expr = CallExpression(expr.location, member, args)
                else:
                    expr = MemberExpression(expr.location, expr, name_token.lexeme)
                continue
            if self._match(TokenType.LEFT_BRACKET):
                index = self.parse_expression()
                self._expect(TokenType.RIGHT_BRACKET, "]")
                expr = IndexExpression(expr.location, expr, index)
                continue
            if self._match(TokenType.LEFT_PAREN) and isinstance(expr, (VariableExpression, MemberExpression)):
                args = self._parse_arg_list("function call")
                expr = CallExpression(expr.location, expr, args)
                continue
            break
        return expr

    def parse_primary(self) -> Expression:
        token = self._peek()
        if token.type == TokenType.INTEGER:
            self._advance()
            return LiteralExpression(token.location, int(token.lexeme))
        if token.type == TokenType.FLOAT:
            self._advance()
            return LiteralExpression(token.location, float(token.lexeme))
        if token.type == TokenType.TRUE:
            self._advance()
            return LiteralExpression(token.location, True)
        if token.type == TokenType.FALSE:
            self._advance()
            return LiteralExpression(token.location, False)
        if token.type == TokenType.NULL:
            self._advance()
            return LiteralExpression(token.location, None)
        if token.type == TokenType.STRING:
            return self._parse_string_or_interpolation()
        if token.type == TokenType.INTERPOLATION_START:
            return self._parse_string_or_interpolation()
        if self._is_name(token) or token.type == TokenType.TYPE_KW:
            self._advance()
            return VariableExpression(token.location, token.lexeme)
        if token.type == TokenType.LEFT_PAREN:
            self._advance()
            expr = self.parse_expression()
            self._expect(TokenType.RIGHT_PAREN, ")")
            return expr
        if token.type == TokenType.LEFT_BRACKET:
            return self._parse_list()
        if token.type == TokenType.LEFT_BRACE:
            return self._parse_hash()
        raise ParseError(self._unexpected_message(token), token.location)

    def _parse_string_or_interpolation(self) -> Expression:
        token = self._peek()
        if token.type == TokenType.STRING:
            first = self._advance()
            if not self._check(TokenType.INTERPOLATION_START):
                return StringLiteralExpression(first.location, first.lexeme)
            parts: list[Expression] = [StringLiteralExpression(first.location, first.lexeme)]
        elif token.type == TokenType.INTERPOLATION_START:
            parts = [StringLiteralExpression(token.location, "")]
        else:
            raise ParseError("Expected string", token.location)

        while self._match(TokenType.INTERPOLATION_START):
            parts.append(self.parse_expression())
            self._expect(TokenType.INTERPOLATION_END, "}")
            if self._check(TokenType.STRING):
                text = self._advance()
                parts.append(StringLiteralExpression(text.location, text.lexeme))
        return StringInterpolation(parts[0].location, parts)

    def _parse_list(self) -> ListLiteral:
        token = self._expect(TokenType.LEFT_BRACKET, "[")
        elements: list[Expression] = []
        while not self._check(TokenType.RIGHT_BRACKET) and not self._check(TokenType.EOF):
            if self._check(TokenType.SEMICOLON):
                raise ParseError("Found ';' inside a list — you may be missing a closing ']'.", self._peek().location)
            elements.append(self.parse_expression())
            self._match(TokenType.COMMA)
        self._expect(TokenType.RIGHT_BRACKET, "]")
        return ListLiteral(token.location, elements)

    def _parse_hash(self) -> HashLiteral:
        token = self._expect(TokenType.LEFT_BRACE, "{")
        pairs: list[HashPair] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._check(TokenType.EOF):
            key_tok = self._peek()
            if key_tok.type == TokenType.SEMICOLON:
                raise ParseError("Found ';' inside a hash — you may be missing a closing '}'.", key_tok.location)
            if key_tok.type == TokenType.STRING:
                key = self._advance().lexeme
            elif self._is_name(key_tok) or key_tok.type == TokenType.TYPE_KW:
                key = self._advance().lexeme
            else:
                raise ParseError(f"Hash keys must be strings or identifiers, but got '{key_tok.lexeme}'.", key_tok.location)
            self._expect(TokenType.COLON, ":")
            value = self.parse_expression()
            pairs.append(HashPair(key, value, key_tok.location))
            self._match(TokenType.COMMA)
        self._expect(TokenType.RIGHT_BRACE, "}")
        return HashLiteral(token.location, pairs)

    def _parse_arg_list(self, context: str) -> list[Argument]:
        args: list[Argument] = []
        seen_keyword = False
        while not self._check(TokenType.RIGHT_PAREN) and not self._check(TokenType.EOF):
            token = self._peek()
            if token.type == TokenType.SEMICOLON:
                raise ParseError(f"Found ';' inside a {context} — you may be missing a closing ')'.", token.location)
            if self._is_name(token) and self._check_offset(1, TokenType.COLON):
                seen_keyword = True
                name = self._advance().lexeme
                self._advance()
                value = self.parse_expression()
                args.append(Argument(value, token.location, name))
            else:
                if seen_keyword:
                    raise ParseError(f"Positional arguments cannot appear after keyword arguments in a {context}.", token.location)
                value = self.parse_expression()
                args.append(Argument(value, token.location))
            self._match(TokenType.COMMA)
        self._expect(TokenType.RIGHT_PAREN, ")")
        return args

    def _parse_type(self) -> TypeAnnotation:
        token = self._peek()
        if token.type == TokenType.LEFT_BRACE:
            return self._parse_object_type()
        if token.type == TokenType.TYPE:
            self._advance()
            return TypeName(token.location, token.lexeme)
        if self._is_name(token):
            self._advance()
            return TypeName(token.location, token.lexeme)
        raise ParseError("Expected type", token.location)

    def _parse_object_type(self) -> ObjectType:
        token = self._expect(TokenType.LEFT_BRACE, "{")
        fields: dict[str, TypeAnnotation] = {}
        while not self._check(TokenType.RIGHT_BRACE) and not self._check(TokenType.EOF):
            field_token = self._expect_name_token("object type field name")
            self._expect(TokenType.COLON, ":")
            fields[field_token.lexeme] = self._parse_type()
            self._match(TokenType.COMMA)
        self._expect(TokenType.RIGHT_BRACE, "}")
        return ObjectType(token.location, fields)

    def _parse_block_body(self) -> list[Statement]:
        body: list[Statement] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._check(TokenType.EOF):
            body.append(self.parse_statement())
        return body

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _peek_offset(self, offset: int) -> Token | None:
        index = self.pos + offset
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    def _advance(self) -> Token:
        token = self._peek()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _check_offset(self, offset: int, type_: TokenType) -> bool:
        token = self._peek_offset(offset)
        return token is not None and token.type == type_

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, type_: TokenType, lexeme: str) -> Token:
        token = self._peek()
        if token.type != type_:
            if token.type == TokenType.EOF:
                raise ParseError(f"Expected {lexeme}, got end of input", token.location)
            help_text = None
            if type_ == TokenType.SEMICOLON:
                help_text = "You may be missing a semicolon ';' at the end of the previous statement."
            elif type_ == TokenType.LEFT_BRACE:
                help_text = "A block opening '{' is missing. Check function, if/else, while, for, or foreach headers."
            elif type_ == TokenType.COLON:
                help_text = "Loop variables must include a type, e.g. 'foreach item: dynamic in items { ... }'."
            raise ParseError(f"Expected {lexeme}, got '{token.lexeme}'", token.location, help_text=help_text)
        return self._advance()

    def _is_name(self, token: Token) -> bool:
        return token.type in (TokenType.IDENTIFIER, TokenType.TYPE)

    def _expect_name(self, expected: str) -> str:
        return self._expect_name_token(expected).lexeme

    def _expect_name_token(self, expected: str) -> Token:
        token = self._peek()
        if not self._is_name(token) and token.type != TokenType.TYPE_KW:
            raise ParseError(f"Expected {expected}, got '{token.lexeme}'", token.location)
        return self._advance()

    def _location(self, token: Token) -> SourceLocation:
        return token.location

    def _unexpected_message(self, token: Token) -> str:
        if token.type == TokenType.EOF:
            return "Unexpected end of file."
        if token.type == TokenType.INTERPOLATION_START:
            return "Found '${' outside a string. Did you forget the opening '\"'?"
        if token.type == TokenType.INTERPOLATION_END:
            return "Found '}' outside a string interpolation."
        if token.lexeme == ";":
            return "Unexpected ';' here — check for an extra semicolon."
        return f"Unexpected '{token.lexeme}' in expression."
