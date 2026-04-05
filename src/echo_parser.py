from __future__ import annotations

from typing import Any, Optional


class Token:
    def __init__(self, type_: str, value: Any, line: Optional[int] = None, col: Optional[int] = None):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        if self.line is not None and self.col is not None:
            return f"{self.type}({self.value}, line={self.line}, col={self.col})"
        return f"{self.type}({self.value})"

class ListLiteral:
    def __init__(self, elements: list[Any]):
        self.elements = elements


class Parser:
    def __init__(self, tokens: list[Any]):
        # Convert string tokens to Token objects if needed
        self.tokens: list[Token] = []
        for token_str in tokens:
            if isinstance(token_str, str):
                # Parse token string like "KEYWORD(fn)" into type and value
                type_end = token_str.find('(')
                value_end = token_str.rfind(')')
                if type_end == -1 or value_end == -1 or value_end <= type_end:
                    raise SyntaxError(f"Invalid token format: {token_str}")
                token_type = token_str[:type_end]
                token_value = token_str[type_end + 1:value_end]
                self.tokens.append(Token(token_type, token_value))
            else:
                token_type = getattr(token_str, "type", None)
                token_value = getattr(token_str, "value", None)
                if token_type is None:
                    raise TypeError(f"Invalid token object: {token_str}")
                token_line = getattr(token_str, "line", None)
                token_col = getattr(token_str, "col", getattr(token_str, "column", None))
                self.tokens.append(Token(token_type, token_value, token_line, token_col))
        self.pos = 0
        self.type_aliases: dict[str, object] = {}

    def peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Token:
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        self.pos += 1
        return tok

    def match(self, *types: str) -> Optional[Token]:
        tok = self.peek()
        if tok and tok.type in types:
            return self.advance()
        return None

    def consume(self) -> Token:
        tok = self.current()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        self.pos += 1
        return tok

    def current(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None  # Indicates end of input

    def _at_end(self) -> bool:
        return self.peek() is None

    def _line_info(self, tok: Optional[Token]) -> str:
        if tok is None:
            return ""
        if tok.line is not None and tok.col is not None:
            return f" at line {tok.line}, column {tok.col}"
        return ""

    def _peek_offset(self, offset: int) -> Optional[Token]:
        index = self.pos + offset
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    def _unexpected_token_msg(self, tok: Optional[Token]) -> str:
        loc = self._line_info(tok)
        if tok is None:
            return "Unexpected end of file."
        if tok.type == "INTERPOLATION_START":
            return (
                f"Line {tok.line}, column {tok.col}: Found '${{' outside a string. "
                "Did you forget the opening '\"' before the string?"
            )
        if tok.type == "INTERPOLATION_END":
            return (
                f"Line {tok.line}, column {tok.col}: Found '}}' outside a string interpolation. "
                "Check for an unmatched '${{...' or a stray '}}'"
            )
        if tok.value == ";":
            return f"Line {tok.line}, column {tok.col}: Unexpected ';' here — check for an extra semicolon."
        return f"Line {tok.line}, column {tok.col}: Unexpected '{tok.value}' in expression."

    def _parse_arg_list(self, context: str = "function call") -> list:
        """Parse a comma-separated argument list, consuming up to and including ')'.
        Raises a clear error if ';' is encountered before ')' is found."""
        args = []
        seen_keyword_arg = False
        while not self._at_end() and not self._is_token("PUNCTUATION", ")"):
            t = self.peek()
            if t is not None and t.type == "PUNCTUATION" and t.value == ";":
                raise SyntaxError(
                    f"Line {t.line}, column {t.col}: "
                    f"Found ';' inside a {context} — you may be missing a closing ')'."
                )

            next_tok = self._peek_offset(1)
            if self._is_name_token(t) and next_tok is not None and next_tok.type == "PUNCTUATION" and next_tok.value == ":":
                seen_keyword_arg = True
                arg_name = self._expect_name("keyword argument name")
                self.expect("PUNCTUATION", ":")
                args.append({"type": "keyword_arg", "name": arg_name, "value": self.parse_expression()})
            else:
                if seen_keyword_arg:
                    raise SyntaxError(
                        f"Line {t.line}, column {t.col}: Positional arguments cannot appear after keyword arguments in a {context}."
                    )
                args.append(self.parse_expression())

            if self._is_token("PUNCTUATION", ","):
                self.advance()
        self.expect("PUNCTUATION", ")")
        return args

    def _is_token(self, type_, value=None):
        tok = self.peek()
        if not tok or tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def _is_name_token(self, tok: Optional[Token]) -> bool:
        return tok is not None and tok.type in ("IDENTIFIER", "METHOD")

    def _is_callable_type_keyword(self, tok: Optional[Token]) -> bool:
        return tok is not None and tok.type == "KEYWORD" and tok.value == "type"

    def _is_method_token(self, tok: Optional[Token]) -> bool:
        return self._is_name_token(tok) or self._is_callable_type_keyword(tok)

    def _expect_name(self, expected: str = "identifier") -> str:
        tok = self.current()
        if not self._is_name_token(tok):
            raise SyntaxError(f"Expected {expected}, got {tok}{self._line_info(tok)}")
        return self.consume().value

    def _parse_type_name(self) -> str:
        tok = self.current()
        if tok is None:
            raise SyntaxError("Expected type, got end of input")
        if tok.type == "DATATYPE":
            return self.consume().value
        if self._is_name_token(tok):
            alias_name = self.consume().value
            if alias_name in self.type_aliases:
                return self.type_aliases[alias_name]
            raise SyntaxError(f"Unknown type alias '{alias_name}'{self._line_info(tok)}")
        raise SyntaxError(f"Expected type, got {tok}{self._line_info(tok)}")

    def _parse_object_type_spec(self):
        self.expect("PUNCTUATION", "{")
        fields = {}

        while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
            field_name = self._expect_name("object type field name")
            self.expect("PUNCTUATION", ":")
            field_type = self._parse_type_name()
            fields[field_name] = field_type

            if self._is_token("PUNCTUATION", ","):
                self.advance()

        self.expect("PUNCTUATION", "}")
        return {"kind": "object", "fields": fields}

    def expect(self, type_, value=None):
        tok = self.current()
        if tok is None:
            raise SyntaxError(f"Expected {type_} {value}, got end of input")
        if tok.type != type_ or (value is not None and tok.value != value):
            raise SyntaxError(f"Expected {type_} {value}, got {tok}{self._line_info(tok)}")
        return self.consume()

    def parse(self):
        statements = []
        while self.peek():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements

    def parse_statement(self):
        token = self.peek()
        if not token:
            return None
            
        # print(f"Parsing statement with token: {token}")
        if token.type == "KEYWORD":
            if token.value == "if":
                return self.parse_if_statement()
            elif token.value == "while":
                return self.parse_while_loop()
            elif token.value == "for":
                return self.parse_for_loop()
            elif token.value == "foreach":
                return self.parse_foreach()
            elif token.value == "fn":
                return self.parse_function()
            elif token.value == "use":
                return self.parse_use_statement()
            elif token.value == "watch":
                return self.parse_watch_statement()
            elif token.value == "type":
                if self._peek_offset(1) is not None and self._peek_offset(1).type == "PUNCTUATION" and self._peek_offset(1).value == "(":
                    expr = self.parse_expression()
                    self.expect("PUNCTUATION", ";")
                    return expr
                return self.parse_type_alias()
            elif token.value == "return":
                self.advance()
                expr = None
                if not self._is_token("PUNCTUATION", ";"):
                    expr = self.parse_expression()
                self.expect("PUNCTUATION", ";")
                return {"type": "return", "value": expr}
            elif token.value == "break":
                self.advance()
                self.expect("PUNCTUATION", ";")
                return {"type": "break"}
            elif token.value == "continue":
                self.advance()
                self.expect("PUNCTUATION", ";")
                return {"type": "continue"}
        elif token.type == "PUNCTUATION" and token.value == "[":
            # Handle list literals with method calls
            expr = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return expr
        elif token.type == "IDENTIFIER" or token.type == "METHOD":
            expr = self.parse_assignment_or_expr()
            return expr
        else:
            line_info = f" at line {token.line}, column {token.col}" if hasattr(token, 'line') and hasattr(token, 'col') else ""
            raise SyntaxError(f"Unexpected token in statement: {token}{line_info}")
            
        return None

    def parse_function(self):
        # print("Starting to parse function")
        self.expect("KEYWORD", "fn")
        # print("Parsed 'fn' keyword")
        name = self._expect_name("function name")
        # print(f"Function name: {name}")
        self.expect("PUNCTUATION", "(")
        # print("Parsed opening parenthesis")
        params = []
        param_types = {}  # Store parameter types
        while not self._at_end() and not self._is_token("PUNCTUATION", ")"):
            param = self._expect_name("parameter name")
            # print(f"Parameter: {param}")
            
            # Check for type annotation
            if self._is_token("PUNCTUATION", ":"):
                self.advance()  # consume the colon
                param_type = self._parse_type_name()
                param_types[param] = param_type
            else:
                raise SyntaxError(f"Type annotation required for parameter '{param}'")
                
            params.append(param)
            if self._is_token("PUNCTUATION", ","):
                self.advance()
                # print("Parsed comma")
        self.expect("PUNCTUATION", ")")
        # print("Parsed closing parenthesis")
        
        return_type = None
        if self._is_token("RETURN_TYPE"):
            self.advance()  # consume the return type arrow
            return_type = self._parse_type_name()
        
        if self._is_token("OPERATOR", "=>"):
            self.advance()
            # print("Parsing inline function")
            body = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            # print("Finished parsing inline function")
            return {"type": "func_def", "name": name, "params": params, "param_types": param_types, "return_type": return_type, "body": body, "inline": True}
        else:
            # print("Parsing function block")
            self.expect("PUNCTUATION", "{")
            # print("Parsed opening brace")
            body = []
            while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
                    # print(f"Added statement to function body: {stmt}")
            self.expect("PUNCTUATION", "}")
            # print("Parsed closing brace")
            # print("Finished parsing function block")
            return {"type": "func_def", "name": name, "params": params, "param_types": param_types, "return_type": return_type, "body": body, "inline": False}

    def parse_assignment_or_expr(self):
        # Get the target identifier
        target_token = self.current()
        target = self._expect_name("identifier")
        target_is_method_name = target_token is not None and target_token.type == "METHOD"
        
        # Check if this is a method call
        if self._is_token("METHOD_OPERATOR", "."):
            self.advance()  # consume the dot
            method_token = self.peek()
            
            if not self._is_method_token(method_token):
                raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{self._line_info(method_token)}")
            
            method = self.advance().value
            self.expect("PUNCTUATION", "(")
            args = self._parse_arg_list(f"'{method}()' call")

            # Create the initial method call
            expr = {"type": "method_call", "target": {"type": "identifier", "name": target}, "method": method, "args": args}

            # Handle method chaining
            while self._is_token("METHOD_OPERATOR", "."):
                self.advance()  # consume the dot
                method_token = self.peek()

                if not self._is_method_token(method_token):
                    raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{self._line_info(method_token)}")

                method = self.advance().value
                self.expect("PUNCTUATION", "(")
                args = self._parse_arg_list(f"'{method}()' call")

                # Create a new method call with the previous expression as the target
                expr = {"type": "method_call", "target": expr, "method": method, "args": args}
            
            # Only expect semicolon at the end of the entire chain
            self.expect("PUNCTUATION", ";")
            return expr
        
        # Check if this is a function call
        if self._is_token("PUNCTUATION", "("):
            # This is a function call
            self.advance()  # consume the opening parenthesis
            args = self._parse_arg_list(f"'{target}()' call")
            self.expect("PUNCTUATION", ";")
            if target_is_method_name:
                # Built-in methods like say()/wait()/ask() are tokenized as METHOD.
                return {"type": "method_call", "method": target, "args": args}
            return {"type": "function_call", "name": target, "args": args}

        # Check if this is an index assignment: identifier[i] = v or identifier[i][j]... = v
        if self._is_token("PUNCTUATION", "["):
            self.advance()  # consume '['
            indices = [self.parse_expression()]
            self.expect("PUNCTUATION", "]")
            while self._is_token("PUNCTUATION", "["):
                self.advance()  # consume '['
                indices.append(self.parse_expression())
                self.expect("PUNCTUATION", "]")
            self.expect("OPERATOR", "=")
            value = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return {"type": "index_assign", "target": target, "indices": indices, "value": value}

        # Check if this is an assignment
        if self._is_token("PUNCTUATION", ":"):
            self.advance()
            var_type = self._parse_type_name()
            # Check if the type is void
            if var_type == "void":
                raise SyntaxError("Cannot use 'void' as a variable type")
        else:
            var_type = None
            
        # Check for assignment operator
        if self._is_token("OPERATOR", "="):
            self.advance()  # consume the equals sign
            value = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return {"type": "assign", "target": target, "var_type": var_type, "value": value}
        else:
            # This is just an identifier expression
            self.expect("PUNCTUATION", ";")
            return {"type": "identifier", "name": target}

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        expr = self.parse_logical_and()
        while self._is_token("OPERATOR", "||"):
            operator = self.advance().value
            right = self.parse_logical_and()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_logical_and(self):
        expr = self.parse_equality()
        while self._is_token("OPERATOR", "&&"):
            operator = self.advance().value
            right = self.parse_equality()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_equality(self):
        expr = self.parse_comparison()
        while self._is_token("OPERATOR", "==") or self._is_token("OPERATOR", "!="):
            operator = self.advance().value
            right = self.parse_comparison()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_comparison(self):
        expr = self.parse_term()
        while (
            self._is_token("OPERATOR", "<")
            or self._is_token("OPERATOR", ">")
            or self._is_token("OPERATOR", "<=")
            or self._is_token("OPERATOR", ">=")
        ):
            operator = self.advance().value
            right = self.parse_term()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        while self._is_token("OPERATOR", "+") or self._is_token("OPERATOR", "-"):
            operator = self.advance().value
            right = self.parse_factor()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_factor(self):
        expr = self.parse_unary()
        while self._is_token("OPERATOR", "*") or self._is_token("OPERATOR", "/") or self._is_token("OPERATOR", "%"):
            operator = self.advance().value
            right = self.parse_unary()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        return expr

    def parse_unary(self):
        if self._is_token("OPERATOR", "!"):
            self.advance()
            operand = self.parse_unary()
            return {"type": "unary", "operator": "!", "operand": operand}
        if self._is_token("OPERATOR", "-"):
            self.advance()
            operand = self.parse_unary()
            return {"type": "unary", "operator": "-", "operand": operand}
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()

        while True:
            if self._is_token("METHOD_OPERATOR", "."):
                self.advance()  # consume the dot
                method_token = self.peek()

                if not self._is_method_token(method_token):
                    raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{self._line_info(method_token)}")

                method = self.advance().value
                self.expect("PUNCTUATION", "(")
                args = self._parse_arg_list(f"'{method}()' call")
                expr = {"type": "method_call", "target": expr, "method": method, "args": args}
                continue

            if self._is_token("PUNCTUATION", "["):
                self.advance()  # consume the opening bracket
                index = self.parse_expression()
                self.expect("PUNCTUATION", "]")
                expr = {"type": "index", "target": expr, "index": index}
                continue

            break

        return expr

    def parse_primary(self):
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input")
        
        if token.type == "METHOD" or token.type == "IDENTIFIER" or self._is_callable_type_keyword(token):
            name_token = self.advance()
            name = name_token.value
            # Check if this is a function call
            if self._is_token("PUNCTUATION", "("):
                self.advance()  # consume the opening parenthesis
                args = self._parse_arg_list(f"'{name}()' call")
                if name_token.type == "METHOD" or self._is_callable_type_keyword(name_token):
                    expr = {"type": "method_call", "method": name, "args": args}
                else:
                    expr = {"type": "function_call", "name": name, "args": args}
            else:
                expr = {"type": "identifier", "name": name}
        
        elif token.type == "NUMBER":
            value = int(self.advance().value)
            expr = {"type": "int", "value": value}
        
        elif token.type == "FLOAT":
            value = float(self.advance().value)
            expr = {"type": "float", "value": value}
        
        elif token.type == "BOOLEAN":
            value = self.advance().value == "true"
            expr = {"type": "boolean", "value": value}

        elif token.type == "NULL":
            self.advance()
            expr = {"type": "null", "value": None}
        
        elif token.type == "STRING":
            value = self.advance().value
            # Check if this is part of a string interpolation
            if self._is_token("INTERPOLATION_START"):
                parts = [{"type": "string", "value": value}]
                while self._is_token("INTERPOLATION_START"):
                    self.advance()  # consume the interpolation start
                    expr_part = self.parse_expression()
                    self.expect("INTERPOLATION_END")
                    parts.append(expr_part)
                    if self._is_token("STRING"):
                        parts.append({"type": "string", "value": self.advance().value})
                expr = {"type": "string_interpolation", "parts": parts}
            else:
                expr = {"type": "string", "value": value}
        
        elif token.type == "PUNCTUATION":
            if token.value == "(":
                self.advance()  # consume the opening parenthesis
                expr = self.parse_expression()
                self.expect("PUNCTUATION", ")")
            elif token.value == "[":
                self.advance()  # consume the opening bracket
                elements = []
                while not self._at_end() and not self._is_token("PUNCTUATION", "]"):
                    if self._is_token("PUNCTUATION", ";"):
                        t = self.peek()
                        raise SyntaxError(
                            f"Line {t.line}, column {t.col}: "
                            "Found ';' inside a list — you may be missing a closing ']'."
                        )
                    elements.append(self.parse_expression())
                    if self._is_token("PUNCTUATION", ","):
                        self.advance()
                self.expect("PUNCTUATION", "]")
                expr = {"type": "list", "elements": elements}
            elif token.value == "{":
                self.advance()  # consume the opening brace
                pairs = []
                while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
                    key_tok = self.peek()
                    if key_tok is None:
                        raise SyntaxError("Unexpected end of input while parsing hash literal")
                    if key_tok.type == "PUNCTUATION" and key_tok.value == ";":
                        raise SyntaxError(
                            f"Line {key_tok.line}, column {key_tok.col}: "
                            "Found ';' inside a hash \u2014 you may be missing a closing '}'.")
                    if key_tok.type == "STRING":
                        key = self.advance().value
                        if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
                            key = key[1:-1]
                    elif key_tok.type == "IDENTIFIER":
                        key = self.advance().value
                    else:
                        raise SyntaxError(
                            f"Line {key_tok.line}, column {key_tok.col}: "
                            f"Hash keys must be strings or identifiers, but got '{key_tok.value}'.")
                    self.expect("PUNCTUATION", ":")
                    value = self.parse_expression()
                    pairs.append({"key": key, "value": value})
                    if self._is_token("PUNCTUATION", ","):
                        self.advance()
                self.expect("PUNCTUATION", "}")
                expr = {"type": "hash", "pairs": pairs}
            elif token.value == ";":
                raise SyntaxError(self._unexpected_token_msg(token))
            else:
                raise SyntaxError(self._unexpected_token_msg(token))
        else:
            raise SyntaxError(self._unexpected_token_msg(token))

        return expr

    def parse_for_loop(self):
        self.expect("KEYWORD", "for")
        var = self._expect_name("loop variable")
        self.expect("PUNCTUATION", ":")
        var_type = self._parse_type_name()
        self.expect("KEYWORD", "in")
        
        # Parse start value (can be a number, float, or identifier)
        start_token = self.peek()
        if not start_token or (start_token.type != "NUMBER" and start_token.type != "FLOAT" and start_token.type != "IDENTIFIER"):
            raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for range start, got {start_token}{self._line_info(start_token)}")
        
        if start_token.type == "IDENTIFIER":
            start = {"type": "identifier", "name": self.advance().value}
        elif start_token.type == "NUMBER":
            start = int(self.advance().value)
        else:
            start = float(self.advance().value)
        
        # Check for range operator
        range_op = self.expect("RANGE_OPERATOR").value
        is_inclusive = len(range_op) == 2  # .. is inclusive, ... is exclusive
        
        # Parse end value (can be a number, float, or identifier)
        end_token = self.peek()
        if not end_token or (end_token.type != "NUMBER" and end_token.type != "FLOAT" and end_token.type != "IDENTIFIER"):
            raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for range end, got {end_token}{self._line_info(end_token)}")
        
        if end_token.type == "IDENTIFIER":
            end = {"type": "identifier", "name": self.advance().value}
        elif end_token.type == "NUMBER":
            end = int(self.advance().value)
        else:
            end = float(self.advance().value)
        
        # Parse step value if present
        by = 1
        if self._is_token("KEYWORD", "by"):
            self.advance()
            # Check for negative number
            if self._is_token("OPERATOR", "-"):
                self.advance()  # Consume the minus operator
                step_token = self.peek()
                if not step_token or (step_token.type != "NUMBER" and step_token.type != "FLOAT" and step_token.type != "IDENTIFIER"):
                    raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for step value, got {step_token}{self._line_info(step_token)}")
                
                if step_token.type == "IDENTIFIER":
                    by = {"type": "unary", "operator": "-", "operand": {"type": "identifier", "name": self.advance().value}}
                elif step_token.type == "NUMBER":
                    by = -int(self.advance().value)
                else:
                    by = -float(self.advance().value)
            else:
                step_token = self.peek()
                if not step_token or (step_token.type != "NUMBER" and step_token.type != "FLOAT" and step_token.type != "IDENTIFIER"):
                    raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for step value, got {step_token}{self._line_info(step_token)}")
                
                if step_token.type == "IDENTIFIER":
                    by = {"type": "identifier", "name": self.advance().value}
                elif step_token.type == "NUMBER":
                    by = int(self.advance().value)
                else:
                    by = float(self.advance().value)
        
        self.expect("PUNCTUATION", "{")
        body = []
        while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
            body.append(self.parse_statement())
        self.expect("PUNCTUATION", "}")
        return {"type": "for", "var": var, "var_type": var_type, "start": start, "end": end, "by": by, "inclusive": is_inclusive, "body": body}

    def parse_foreach(self):
        # print("Starting to parse foreach loop")
        self.expect("KEYWORD", "foreach")
        var = self._expect_name("loop variable")
        self.expect("PUNCTUATION", ":")
        var_type = self._parse_type_name()
        # print(f"Foreach loop variable: {var}")
        self.expect("KEYWORD", "in")
        iterable = self.parse_expression()  # Allow expressions for iterables, not just identifiers
        # print(f"Iterable expression: {iterable}")
        self.expect("PUNCTUATION", "{")
        body = []
        while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to foreach body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing foreach loop")
        return {"type": "foreach", "var": var, "var_type": var_type, "iterable": iterable, "body": body}

    def parse_method_call(self):
        method = self.advance().value
        self.expect("PUNCTUATION", "(")
        args = []
        while not self._at_end() and not self._is_token("PUNCTUATION", ")"):
            args.append(self.parse_expression())
            if self._is_token("PUNCTUATION", ","):
                self.advance()
        self.expect("PUNCTUATION", ")")
        self.expect("PUNCTUATION", ";")
        return {"type": "method_call", "method": method, "args": args}

    def parse_type_alias(self):
        self.expect("KEYWORD", "type")
        alias_name = self._expect_name("type alias name")
        self.expect("OPERATOR", "=")

        if self._is_token("PUNCTUATION", "{"):
            target_type = self._parse_object_type_spec()
        else:
            target_type = self._parse_type_name()

        self.expect("PUNCTUATION", ";")

        if alias_name in ("int", "float", "str", "bool", "dynamic", "list", "hash", "void"):
            raise SyntaxError(f"Cannot redefine built-in type '{alias_name}'")

        if alias_name in self.type_aliases:
            raise SyntaxError(f"Type alias '{alias_name}' is already defined")

        self.type_aliases[alias_name] = target_type
        return None

    def parse_if_statement(self):
        # print("Starting to parse if statement")
        self.expect("KEYWORD", "if")
        condition = self.parse_expression()
        # print(f"If condition: {condition}")
        self.expect("PUNCTUATION", "{")
        body = []
        while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to if body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing if body")
        
        # Check for else if or else
        result = {"type": "if", "condition": condition, "body": body}
        
        # Handle else if and else
        if self._is_token("KEYWORD", "else"):
            self.advance()  # consume 'else'
            
            # Check if this is an 'else if'
            if self._is_token("KEYWORD", "if"):
                # print("Found else if")
                else_if = self.parse_if_statement()  # Parse the else-if as a complete if statement
                result["else_body"] = [else_if]  # Wrap in a list to match expected body format
            else:
                # This is just an 'else'
                # print("Found else")
                self.expect("PUNCTUATION", "{")
                else_body = []
                while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
                    stmt = self.parse_statement()
                    if stmt:
                        else_body.append(stmt)
                        # print(f"Added statement to else body: {stmt}")
                self.expect("PUNCTUATION", "}")
                result["else_body"] = else_body
                # print("Finished parsing else body")
        
        return result

    def parse_return(self):
        self.expect("KEYWORD", "return")
        value = None
        if not self._is_token("PUNCTUATION", ";"):
            value = self.parse_expression()
        self.expect("PUNCTUATION", ";")
        return {"type": "return", "value": value}

    def parse_break(self):
        self.expect("KEYWORD", "break")
        self.expect("PUNCTUATION", ";")
        return {"type": "break"}

    def parse_continue(self):
        self.expect("KEYWORD", "continue")
        self.expect("PUNCTUATION", ";")
        return {"type": "continue"}

    def parse_while_loop(self):
        # print("Starting to parse while loop")
        self.expect("KEYWORD", "while")
        condition = self.parse_expression()
        # print(f"While loop condition: {condition}")
        self.expect("PUNCTUATION", "{")
        body = []
        while not self._at_end() and not self._is_token("PUNCTUATION", "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to while body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing while loop")
        return {"type": "while", "condition": condition, "body": body}

    def parse_use_statement(self):
        self.expect("KEYWORD", "use")
        
        # Check for mut keyword
        is_mutable = False
        if self._is_token("KEYWORD", "mut"):
            self.advance()  # consume 'mut'
            is_mutable = True
            
        # Get the first variable name
        variables = []
        var_name = self.expect("IDENTIFIER").value
        variables.append(var_name)
        
        # Parse additional variables if comma-separated
        while self._is_token("PUNCTUATION", ","):
            self.advance()  # consume comma
            var_name = self.expect("IDENTIFIER").value
            variables.append(var_name)
            
        self.expect("PUNCTUATION", ";")
        
        return {
            "type": "use_statement",
            "variables": variables,
            "is_mutable": is_mutable
        }

    def parse_watch_statement(self):
        self.expect("KEYWORD", "watch")
        variables = []
        
        # Parse first variable
        var = self.expect("IDENTIFIER").value
        variables.append(var)
        
        # Parse additional variables if comma-separated
        while self._is_token("PUNCTUATION", ","):
            self.advance()  # consume comma
            var = self.expect("IDENTIFIER").value
            variables.append(var)
            
        self.expect("PUNCTUATION", ";")
        return {"type": "watch_statement", "variables": variables}