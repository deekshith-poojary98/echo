from __future__ import annotations

from pathlib import Path

from echo.errors import LexError, SourceLocation
from echo.frontend.tokens import KEYWORDS, TYPE_NAMES, Token, TokenType


class Lexer:
    def tokenize(self, source: str, filename: str | None = "<input>") -> list[Token]:
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        tokens: list[Token] = []

        while not self._at_end():
            self._skip_whitespace_and_comments()
            if self._at_end():
                break
            tokens.extend(self._next_tokens())

        tokens.append(self._make_token(TokenType.EOF, ""))
        return tokens

    def tokenize_file(self, path: str | Path) -> list[Token]:
        file_path = Path(path)
        return self.tokenize(file_path.read_text(encoding="utf-8"), filename=str(file_path))

    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self, offset: int = 0) -> str:
        index = self.pos + offset
        if index >= len(self.source):
            return "\0"
        return self.source[index]

    def _advance(self) -> str:
        char = self.source[self.pos]
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def _make_token(self, type_: TokenType, lexeme: str, line: int | None = None, column: int | None = None) -> Token:
        return Token(type_, lexeme, line or self.line, column if column is not None else self.column, self.filename)

    def _error(self, message: str, line: int | None = None, column: int | None = None) -> None:
        raise LexError(
            message,
            SourceLocation(line or self.line, column or self.column, self.filename),
        )

    def _skip_whitespace_and_comments(self) -> None:
        while not self._at_end():
            char = self._peek()
            if char in " \t\r\n":
                self._advance()
                continue
            if char == "/" and self._peek(1) == "/":
                while not self._at_end() and self._peek() != "\n":
                    self._advance()
                continue
            if char == "/" and self._peek(1) == "*":
                start_line, start_col = self.line, self.column
                self._advance()
                self._advance()
                closed = False
                while not self._at_end():
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        closed = True
                        break
                    self._advance()
                if not closed:
                    self._error("Unterminated block comment", start_line, start_col)
                continue
            break

    def _next_tokens(self) -> list[Token]:
        char = self._peek()
        if char in ('"', "'"):
            return self._string()
        if char.isdigit() or (char == "." and self._peek(1).isdigit()):
            return [self._number()]
        if char.isalpha() or char == "_":
            return [self._identifier()]
        return [self._operator_or_punct()]

    def _identifier(self) -> Token:
        start_line, start_col = self.line, self.column
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        lexeme = self.source[start:self.pos]
        if lexeme in KEYWORDS:
            token_type = KEYWORDS[lexeme]
        elif lexeme in TYPE_NAMES:
            token_type = TokenType.TYPE
        else:
            token_type = TokenType.IDENTIFIER
        return Token(token_type, lexeme, start_line, start_col, self.filename)

    def _number(self) -> Token:
        start_line, start_col = self.line, self.column
        start = self.pos
        is_float = False

        if self._peek() == ".":
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        else:
            while self._peek().isdigit():
                self._advance()
            if self._peek() == "." and self._peek(1).isdigit():
                is_float = True
                self._advance()
                while self._peek().isdigit():
                    self._advance()

        if self._peek() in "eE":
            sign = self._peek(1)
            digits_at = 2 if sign in "+-" else 1
            if self._peek(digits_at).isdigit():
                is_float = True
                self._advance()
                if self._peek() in "+-":
                    self._advance()
                while self._peek().isdigit():
                    self._advance()

        lexeme = self.source[start:self.pos]
        token_type = TokenType.FLOAT if is_float else TokenType.INTEGER
        return Token(token_type, lexeme, start_line, start_col, self.filename)

    def _string(self) -> list[Token]:
        quote = self._advance()
        triple = self._peek() == quote and self._peek(1) == quote
        if triple:
            self._advance()
            self._advance()
        start_line, start_col = self.line, self.column - (3 if triple else 1)
        parts: list[Token] = []
        text_start = self.pos
        text_line, text_col = self.line, self.column

        def flush_text(end: int) -> None:
            nonlocal text_start, text_line, text_col
            text = self.source[text_start:end]
            parts.append(Token(TokenType.STRING, text, text_line, text_col, self.filename))

        while not self._at_end():
            char = self._peek()
            if char == "\n" and not triple:
                self._error(f"Unterminated string; did you forget a closing {quote}?", start_line, start_col)
            if char == "\\":
                self._advance()
                if self._at_end() or (self._peek() == "\n" and not triple):
                    self._error("Unterminated string escape sequence", start_line, start_col)
                self._advance()
                continue
            if self.source.startswith("${", self.pos):
                flush_text(self.pos)
                interp_line, interp_col = self.line, self.column
                self._advance()
                self._advance()
                parts.append(Token(TokenType.INTERPOLATION_START, "${", interp_line, interp_col, self.filename))
                parts.extend(self._interpolation_expression())
                if self._peek() != "}":
                    self._error("Missing closing brace in string interpolation", interp_line, interp_col)
                end_line, end_col = self.line, self.column
                self._advance()
                parts.append(Token(TokenType.INTERPOLATION_END, "}", end_line, end_col, self.filename))
                text_start = self.pos
                text_line, text_col = self.line, self.column
                continue
            if char == quote:
                if triple:
                    if self._peek(1) == quote and self._peek(2) == quote:
                        flush_text(self.pos)
                        self._advance()
                        self._advance()
                        self._advance()
                        if not parts:
                            parts.append(Token(TokenType.STRING, "", start_line, start_col, self.filename))
                        return parts
                    self._advance()
                    continue
                flush_text(self.pos)
                self._advance()
                if not parts:
                    parts.append(Token(TokenType.STRING, "", start_line, start_col, self.filename))
                return parts
            self._advance()

        closer = quote * 3 if triple else quote
        self._error(f"Unterminated string; did you forget a closing {closer}?", start_line, start_col)
        return []

    def _interpolation_expression(self) -> list[Token]:
        depth = 0
        start = self.pos
        start_line, start_col = self.line, self.column
        while not self._at_end():
            char = self._peek()
            if char == "{":
                depth += 1
                self._advance()
                continue
            if char == "}":
                if depth == 0:
                    break
                depth -= 1
                self._advance()
                continue
            if char in ('"', "'"):
                # Allow nested quotes inside interpolation by scanning them.
                quote = self._advance()
                while not self._at_end() and self._peek() != quote:
                    if self._peek() == "\\":
                        self._advance()
                    if self._peek() == "\n":
                        self._error("Unterminated string in interpolation", start_line, start_col)
                    self._advance()
                if self._peek() == quote:
                    self._advance()
                continue
            if char == "\n":
                self._error("Unterminated string interpolation", start_line, start_col)
            self._advance()

        expr_source = self.source[start:self.pos]
        inner = Lexer().tokenize(expr_source, filename=self.filename)
        shifted: list[Token] = []
        for token in inner:
            if token.type == TokenType.EOF:
                continue
            shifted.append(
                Token(
                    token.type,
                    token.lexeme,
                    start_line + token.line - 1,
                    start_col + token.column - 1 if token.line == 1 else token.column,
                    self.filename,
                )
            )
        return shifted

    def _operator_or_punct(self) -> Token:
        start_line, start_col = self.line, self.column
        char = self._advance()
        nxt = self._peek()

        two = char + nxt
        two_map = {
            "==": TokenType.EQUAL_EQUAL,
            "!=": TokenType.BANG_EQUAL,
            "<=": TokenType.LESS_EQUAL,
            ">=": TokenType.GREATER_EQUAL,
            "&&": TokenType.AND_AND,
            "||": TokenType.OR_OR,
            "->": TokenType.ARROW,
            "=>": TokenType.FAT_ARROW,
            "+=": TokenType.PLUS_EQUAL,
            "-=": TokenType.MINUS_EQUAL,
            "*=": TokenType.STAR_EQUAL,
            "/=": TokenType.SLASH_EQUAL,
            "%=": TokenType.PERCENT_EQUAL,
        }
        if two in two_map:
            self._advance()
            return Token(two_map[two], two, start_line, start_col, self.filename)

        if char == ".":
            if nxt == ".":
                self._advance()
                if self._peek() == ".":
                    self._advance()
                    return Token(TokenType.DOT_DOT_DOT, "...", start_line, start_col, self.filename)
                return Token(TokenType.DOT_DOT, "..", start_line, start_col, self.filename)
            return Token(TokenType.DOT, ".", start_line, start_col, self.filename)

        single = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "=": TokenType.EQUAL,
            "<": TokenType.LESS,
            ">": TokenType.GREATER,
            "!": TokenType.BANG,
            "(": TokenType.LEFT_PAREN,
            ")": TokenType.RIGHT_PAREN,
            "{": TokenType.LEFT_BRACE,
            "}": TokenType.RIGHT_BRACE,
            "[": TokenType.LEFT_BRACKET,
            "]": TokenType.RIGHT_BRACKET,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            ";": TokenType.SEMICOLON,
        }
        if char in single:
            return Token(single[char], char, start_line, start_col, self.filename)

        self._error(f"Invalid token '{char}'", start_line, start_col)
        return self._make_token(TokenType.EOF, "")
