class Token:
    def __init__(self, type_, value, line=None, col=None):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        if self.line is not None and self.col is not None:
            return f"{self.type}({self.value}, line={self.line}, col={self.col})"
        return f"{self.type}({self.value})"

class ListLiteral:
    def __init__(self, elements):
        self.elements = elements


class Parser:
    def __init__(self, tokens):
        # Convert string tokens to Token objects if needed
        self.tokens = []
        for token_str in tokens:
            if isinstance(token_str, str):
                # Parse token string like "KEYWORD(fn)" into type and value
                type_end = token_str.index('(')
                value_end = token_str.index(')')
                token_type = token_str[:type_end]
                token_value = token_str[type_end + 1:value_end]
                self.tokens.append(Token(token_type, token_value))
            else:
                # Handle tokens that already have line and column info
                if hasattr(token_str, 'line') and hasattr(token_str, 'col'):
                    self.tokens.append(Token(token_str.type, token_str.value, token_str.line, token_str.col))
                else:
                    self.tokens.append(token_str)
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def match(self, *types):
        tok = self.peek()
        if tok and tok.type in types:
            return self.advance()
        return None

    def consume(self):
        tok = self.current()
        self.pos += 1
        return tok

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None  # Indicates end of input

    def expect(self, type_, value=None):
        tok = self.current()
        if tok is None:
            raise SyntaxError(f"Expected {type_} {value}, got end of input")
        if tok.type != type_ or (value is not None and tok.value != value):
            line_info = f" at line {tok.line}, column {tok.col}" if hasattr(tok, 'line') and hasattr(tok, 'col') else ""
            raise SyntaxError(f"Expected {type_} {value}, got {tok}{line_info}")
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
                # print("Recognized foreach keyword, calling parse_foreach")
                return self.parse_foreach()
            elif token.value == "fn":
                # print("Recognized fn keyword, calling parse_function")
                return self.parse_function()
            elif token.value == "return":
                self.advance()
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
                
        elif token.type == "METHOD":
            expr = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return expr
            
        elif token.type == "IDENTIFIER":
            # Check if this is a function call
            next_token = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_token and next_token.type == "PUNCTUATION" and next_token.value == "(":
                # This is a function call
                name = self.advance().value
                self.advance()  # consume the opening parenthesis
                args = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                    args.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", ")")
                self.expect("PUNCTUATION", ";")
                return {"type": "function_call", "name": name, "args": args}
            else:
                # This is an assignment or expression
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
        name = self.expect("IDENTIFIER").value
        # print(f"Function name: {name}")
        self.expect("PUNCTUATION", "(")
        # print("Parsed opening parenthesis")
        params = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
            param = self.expect("IDENTIFIER").value
            # print(f"Parameter: {param}")
            params.append(param)
            if self.peek() and self.peek().value == ",":
                self.advance()
                # print("Parsed comma")
        self.expect("PUNCTUATION", ")")
        # print("Parsed closing parenthesis")
        
        if self.match("OPERATOR") and self.tokens[self.pos - 1].value == "=>":
            # print("Parsing inline function")
            body = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            # print("Finished parsing inline function")
            return {"type": "func_def", "name": name, "params": params, "body": body, "inline": True}
        else:
            # print("Parsing function block")
            self.expect("PUNCTUATION", "{")
            # print("Parsed opening brace")
            body = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
                    # print(f"Added statement to function body: {stmt}")
            self.expect("PUNCTUATION", "}")
            # print("Parsed closing brace")
            # print("Finished parsing function block")
            return {"type": "func_def", "name": name, "params": params, "body": body, "inline": False}

    def parse_assignment_or_expr(self):
        # Check if this is a method call
        if self.peek() and self.peek().type == "METHOD":
            method = self.advance().value
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            
            # Check if there's a method chain
            if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == ".":
                node = {"type": "method_call", "method": method, "args": args}
                self.advance()  # consume the dot
                method_token = self.peek()
                
                if not method_token or (method_token.type != "METHOD" and method_token.type != "IDENTIFIER"):
                    line_info = f" at line {method_token.line}, column {method_token.col}" if hasattr(method_token, 'line') and hasattr(method_token, 'col') else ""
                    raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{line_info}")
                
                chain_method = self.advance().value
                self.expect("PUNCTUATION", "(")
                chain_args = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                    chain_args.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", ")")
                self.expect("PUNCTUATION", ";")
                return {"type": "method_call", "target": node, "method": chain_method, "args": chain_args}
            else:
                self.expect("PUNCTUATION", ";")
                return {"type": "method_call", "method": method, "args": args}
        
        # Get the target identifier
        target = self.expect("IDENTIFIER").value
        
        # Check if this is a function call
        if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == "(":
            # This is a function call
            self.advance()  # consume the opening parenthesis
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            self.expect("PUNCTUATION", ";")
            return {"type": "function_call", "name": target, "args": args}
        
        # Check if this is an assignment
        if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == ":":
            self.advance()
            var_type = self.expect("DATATYPE").value
        else:
            var_type = None
            
        # Check for assignment operator
        if self.peek() and self.peek().type == "OPERATOR" and self.peek().value == "=":
            self.advance()  # consume the equals sign
            value = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return {"type": "assign", "target": target, "var_type": var_type, "value": value}
        else:
            # This is just an identifier expression
            self.expect("PUNCTUATION", ";")
            return {"type": "identifier", "name": target}

    def parse_expression(self):
        # print("Starting to parse expression")
        # Parse the primary expression first
        expr = self.parse_primary()
        # print(f"Primary expression: {expr}")
        
        # Handle method chaining
        while self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == ".":
            # print("Found method chaining")
            self.advance()  # consume the dot
            method_token = self.peek()
            
            if not method_token or (method_token.type != "METHOD" and method_token.type != "IDENTIFIER"):
                line_info = f" at line {method_token.line}, column {method_token.col}" if hasattr(method_token, 'line') and hasattr(method_token, 'col') else ""
                raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{line_info}")
            
            method = self.advance().value
            # print(f"Method name: {method}")
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            # print(f"Method arguments: {args}")
            
            # Create a new method call node with the previous expression as the target
            expr = {"type": "method_call", "target": expr, "method": method, "args": args}
            # print(f"Updated expression after method call: {expr}")
        
        # Handle binary operators
        while self.peek() and self.peek().type == "OPERATOR":
            # print(f"Found binary operator: {self.peek().value}")
            operator = self.advance().value
            right = self.parse_primary()
            # print(f"Right operand: {right}")
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
            # print(f"Updated expression after binary operation: {expr}")
        
        # print(f"Final expression: {expr}")
        return expr

    def parse_primary(self):
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input")
            
        # print(f"Parsing primary with token: {token}")
        if token.type == "METHOD":
            method = self.advance().value
            # print(f"Method name: {method}")
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            # print(f"Method arguments: {args}")
            return {"type": "method_call", "method": method, "args": args}
            
        elif token.type == "IDENTIFIER":
            name = self.advance().value
            # print(f"Identifier: {name}")
            # Check if this is a function call
            if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == "(":
                # print(f"Found function call for {name}")
                self.advance()  # consume the opening parenthesis
                args = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                    args.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", ")")
                # print(f"Function arguments: {args}")
                return {"type": "function_call", "name": name, "args": args}
            else:
                return {"type": "identifier", "name": name}
            
        elif token.type == "NUMBER":
            value = float(self.advance().value)
            # print(f"Number: {value}")
            return {"type": "int", "value": value}
            
        elif token.type == "FLOAT":
            value = float(self.advance().value)
            # print(f"Float: {value}")
            return {"type": "float", "value": value}
            
        elif token.type == "BOOLEAN":
            value = self.advance().value == "true"
            # print(f"Boolean: {value}")
            return {"type": "boolean", "value": value}
            
        elif token.type == "STRING":
            value = self.advance().value
            # print(f"String: {value}")
            
            # Check if this is part of a string interpolation
            if self.peek() and self.peek().type == "INTERPOLATION_START":
                # print("Found string interpolation")
                parts = [{"type": "string", "value": value}]
                
                # Parse all interpolation parts
                while self.peek() and self.peek().type == "INTERPOLATION_START":
                    self.advance()  # consume the interpolation start
                    var_name = self.expect("IDENTIFIER").value
                    self.expect("INTERPOLATION_END")
                    parts.append({"type": "identifier", "name": var_name})
                    
                    # Check if there's more string after the interpolation
                    if self.peek() and self.peek().type == "STRING":
                        parts.append({"type": "string", "value": self.advance().value})
                
                return {"type": "string_interpolation", "parts": parts}
            else:
                return {"type": "string", "value": value}
            
        elif token.type == "PUNCTUATION":
            if token.value == "(":
                # print("Found parenthesized expression")
                self.advance()  # consume the opening parenthesis
                expr = self.parse_expression()
                self.expect("PUNCTUATION", ")")
                return expr
            elif token.value == "[":
                # print("Found list literal")
                self.advance()  # consume the opening bracket
                elements = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "]"):
                    elements.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", "]")
                return {"type": "list", "elements": elements}
            elif token.value == "{":
                # print("Found hash literal")
                self.advance()  # consume the opening brace
                pairs = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
                    # Handle both string and identifier keys
                    key_tok = self.peek()
                    if key_tok.type == "STRING":
                        key = self.advance().value
                        if key.startswith('"') and key.endswith('"'):
                            key = key[1:-1]
                    elif key_tok.type == "IDENTIFIER":
                        key = self.advance().value
                    else:
                        line_info = f" at line {key_tok.line}, column {key_tok.col}" if hasattr(key_tok, 'line') and hasattr(key_tok, 'col') else ""
                        raise SyntaxError(f"Expected STRING or IDENTIFIER as key, got {key_tok}{line_info}")
                    
                    self.expect("PUNCTUATION", ":")
                    value = self.parse_expression()
                    pairs.append({"key": key, "value": value})
                    
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                
                self.expect("PUNCTUATION", "}")
                return {"type": "hash", "pairs": pairs}
            # Handle unexpected semicolon specifically
            elif token.value == ";":
                line_info = f" at line {token.line}, column {token.col}" if hasattr(token, 'line') and hasattr(token, 'col') else ""
                raise SyntaxError(f"Unexpected semicolon in expression: {token}{line_info}")
            
        # If we reach here, it's an unexpected token
        line_info = f" at line {token.line}, column {token.col}" if hasattr(token, 'line') and hasattr(token, 'col') else ""
        raise SyntaxError(f"Unexpected token in expression: {token}{line_info}")

    def parse_for_loop(self):
        self.expect("KEYWORD", "for")
        var = self.expect("IDENTIFIER").value
        self.expect("KEYWORD", "in")
        
        # Handle both NUMBER and FLOAT tokens for start value
        start_token = self.peek()
        if not start_token or (start_token.type != "NUMBER" and start_token.type != "FLOAT"):
            line_info = f" at line {start_token.line}, column {start_token.col}" if hasattr(start_token, 'line') and hasattr(start_token, 'col') else ""
            raise SyntaxError(f"Expected NUMBER or FLOAT for range start, got {start_token}{line_info}")
        start = float(self.advance().value)
        
        self.expect("PUNCTUATION", ".")
        self.expect("PUNCTUATION", ".")
        
        # Handle both NUMBER and FLOAT tokens for end value
        end_token = self.peek()
        if not end_token or (end_token.type != "NUMBER" and end_token.type != "FLOAT"):
            line_info = f" at line {end_token.line}, column {end_token.col}" if hasattr(end_token, 'line') and hasattr(end_token, 'col') else ""
            raise SyntaxError(f"Expected NUMBER or FLOAT for range end, got {end_token}{line_info}")
        end = float(self.advance().value)
        
        by = 1
        if self.match("KEYWORD") and self.tokens[self.pos - 1].value == "by":
            # Handle both NUMBER and FLOAT tokens for step value
            step_token = self.peek()
            if not step_token or (step_token.type != "NUMBER" and step_token.type != "FLOAT"):
                line_info = f" at line {step_token.line}, column {step_token.col}" if hasattr(step_token, 'line') and hasattr(step_token, 'col') else ""
                raise SyntaxError(f"Expected NUMBER or FLOAT for step value, got {step_token}{line_info}")
            by = float(self.advance().value)
        
        self.expect("PUNCTUATION", "{")
        body = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
            body.append(self.parse_statement())
        self.expect("PUNCTUATION", "}")
        return {"type": "for", "var": var, "start": start, "end": end, "by": by, "body": body}

    def parse_foreach(self):
        # print("Starting to parse foreach loop")
        self.expect("KEYWORD", "foreach")
        var = self.expect("IDENTIFIER").value
        # print(f"Foreach loop variable: {var}")
        self.expect("KEYWORD", "in")
        iterable = self.parse_expression()  # Allow expressions for iterables, not just identifiers
        # print(f"Iterable expression: {iterable}")
        self.expect("PUNCTUATION", "{")
        body = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to foreach body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing foreach loop")
        return {"type": "foreach", "var": var, "iterable": iterable, "body": body}

    def parse_method_call(self):
        method = self.advance().value
        self.expect("PUNCTUATION", "(")
        args = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
            args.append(self.parse_expression())
            if self.peek() and self.peek().value == ",":
                self.advance()
        self.expect("PUNCTUATION", ")")
        self.expect("PUNCTUATION", ";")
        return {"type": "method_call", "method": method, "args": args}

    def parse_if_statement(self):
        # print("Starting to parse if statement")
        self.expect("KEYWORD", "if")
        condition = self.parse_expression()
        # print(f"If condition: {condition}")
        self.expect("PUNCTUATION", "{")
        body = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to if body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing if body")
        
        # Check for else if or else
        result = {"type": "if", "condition": condition, "body": body}
        
        # Handle else if and else
        if self.peek() and self.peek().type == "KEYWORD" and self.peek().value == "else":
            self.advance()  # consume 'else'
            
            # Check if this is an 'else if'
            if self.peek() and self.peek().type == "KEYWORD" and self.peek().value == "if":
                # print("Found else if")
                else_if = self.parse_if_statement()  # Parse the else-if as a complete if statement
                result["else_body"] = [else_if]  # Wrap in a list to match expected body format
            else:
                # This is just an 'else'
                # print("Found else")
                self.expect("PUNCTUATION", "{")
                else_body = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
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
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
                # print(f"Added statement to while body: {stmt}")
        self.expect("PUNCTUATION", "}")
        # print("Finished parsing while loop")
        return {"type": "while", "condition": condition, "body": body}