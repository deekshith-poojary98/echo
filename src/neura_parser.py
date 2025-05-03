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
                return self.parse_foreach()
            elif token.value == "fn":
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
        elif token.type == "PUNCTUATION" and token.value == "[":
            # Handle list literals with method calls
            expr = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return expr
        elif token.type == "METHOD":
            expr = self.parse_expression()
            self.expect("PUNCTUATION", ";")
            return expr
        elif token.type == "IDENTIFIER":
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
        param_types = {}  # Store parameter types
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
            param = self.expect("IDENTIFIER").value
            # print(f"Parameter: {param}")
            
            # Check for type annotation
            if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == ":":
                self.advance()  # consume the colon
                param_type = self.expect("DATATYPE").value
                param_types[param] = param_type
            else:
                raise SyntaxError(f"Type annotation required for parameter '{param}'")
                
            params.append(param)
            if self.peek() and self.peek().value == ",":
                self.advance()
                # print("Parsed comma")
        self.expect("PUNCTUATION", ")")
        # print("Parsed closing parenthesis")
        
        # Require return type annotation
        if not (self.peek() and self.peek().type == "RETURN_TYPE"):
            raise SyntaxError(f"Return type annotation required for function '{name}'")
        
        self.advance()  # consume the return type arrow
        return_type = self.expect("DATATYPE").value
        
        if self.match("OPERATOR") and self.tokens[self.pos - 1].value == "=>":
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
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
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
        target = self.expect("IDENTIFIER").value
        
        # Check if this is a method call
        if self.peek() and self.peek().type == "METHOD_OPERATOR":
            self.advance()  # consume the dot
            method_token = self.peek()
            
            if not method_token or (method_token.type != "METHOD" and method_token.type != "IDENTIFIER"):
                line_info = f" at line {method_token.line}, column {method_token.col}" if hasattr(method_token, 'line') and hasattr(method_token, 'col') else ""
                raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{line_info}")
            
            method = self.advance().value
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            self.expect("PUNCTUATION", ";")
            return {"type": "method_call", "target": {"type": "identifier", "name": target}, "method": method, "args": args}
        
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
            # Check if the type is void
            if var_type == "void":
                raise SyntaxError("Cannot use 'void' as a variable type")
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
        # Parse the primary expression first
        expr = self.parse_primary()
        
        # Handle method chaining
        while self.peek() and self.peek().type == "METHOD_OPERATOR":
            self.advance()  # consume the dot
            method_token = self.peek()
            
            if not method_token or (method_token.type != "METHOD" and method_token.type != "IDENTIFIER"):
                line_info = f" at line {method_token.line}, column {method_token.col}" if hasattr(method_token, 'line') and hasattr(method_token, 'col') else ""
                raise SyntaxError(f"Expected METHOD or IDENTIFIER after '.', got {method_token}{line_info}")
            
            method = self.advance().value
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            
            # Create a new method call node with the previous expression as the target
            expr = {"type": "method_call", "target": expr, "method": method, "args": args}
        
        # Handle binary operators
        while self.peek() and self.peek().type == "OPERATOR":
            operator = self.advance().value
            right = self.parse_primary()
            expr = {"type": "binary", "operator": operator, "left": expr, "right": right}
        
        return expr

    def parse_primary(self):
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input")
            
        # Handle unary operators
        if token.type == "OPERATOR" and token.value == "!":
            self.advance()  # consume the operator
            operand = self.parse_primary()
            return {"type": "unary", "operator": "!", "operand": operand}
            
        if token.type == "METHOD":
            method = self.advance().value
            self.expect("PUNCTUATION", "(")
            args = []
            while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                args.append(self.parse_expression())
                if self.peek() and self.peek().value == ",":
                    self.advance()
            self.expect("PUNCTUATION", ")")
            return {"type": "method_call", "method": method, "args": args}
            
        elif token.type == "IDENTIFIER":
            name = self.advance().value
            # Check if this is a function call
            if self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == "(":
                self.advance()  # consume the opening parenthesis
                args = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == ")"):
                    args.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", ")")
                return {"type": "function_call", "name": name, "args": args}
            # Check for indexing
            elif self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == "[":
                self.advance()  # consume the opening bracket
                index = self.parse_expression()
                self.expect("PUNCTUATION", "]")
                return {"type": "index", "target": {"type": "identifier", "name": name}, "index": index}
            else:
                return {"type": "identifier", "name": name}
            
        elif token.type == "NUMBER":
            value = float(self.advance().value)
            return {"type": "int", "value": value}
            
        elif token.type == "FLOAT":
            value = float(self.advance().value)
            return {"type": "float", "value": value}
            
        elif token.type == "BOOLEAN":
            value = self.advance().value == "true"
            return {"type": "boolean", "value": value}
            
        elif token.type == "STRING":
            value = self.advance().value
            
            # Check if this is part of a string interpolation
            if self.peek() and self.peek().type == "INTERPOLATION_START":
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
            # Check for indexing
            elif self.peek() and self.peek().type == "PUNCTUATION" and self.peek().value == "[":
                self.advance()  # consume the opening bracket
                index = self.parse_expression()
                self.expect("PUNCTUATION", "]")
                return {"type": "index", "target": {"type": "string", "value": value}, "index": index}
            else:
                return {"type": "string", "value": value}
            
        elif token.type == "PUNCTUATION":
            if token.value == "(":
                self.advance()  # consume the opening parenthesis
                expr = self.parse_expression()
                self.expect("PUNCTUATION", ")")
                return expr
            elif token.value == "[":
                self.advance()  # consume the opening bracket
                elements = []
                while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "]"):
                    elements.append(self.parse_expression())
                    if self.peek() and self.peek().value == ",":
                        self.advance()
                self.expect("PUNCTUATION", "]")
                return {"type": "list", "elements": elements}
            elif token.value == "{":
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
        
        # Parse start value (can be a number, float, or identifier)
        start_token = self.peek()
        if not start_token or (start_token.type != "NUMBER" and start_token.type != "FLOAT" and start_token.type != "IDENTIFIER"):
            line_info = f" at line {start_token.line}, column {start_token.col}" if hasattr(start_token, 'line') and hasattr(start_token, 'col') else ""
            raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for range start, got {start_token}{line_info}")
        
        if start_token.type == "IDENTIFIER":
            start = {"type": "identifier", "name": self.advance().value}
        else:
            start = float(self.advance().value)
        
        # Check for range operator
        range_op = self.expect("RANGE_OPERATOR").value
        is_inclusive = len(range_op) == 2  # .. is inclusive, ... is exclusive
        
        # Parse end value (can be a number, float, or identifier)
        end_token = self.peek()
        if not end_token or (end_token.type != "NUMBER" and end_token.type != "FLOAT" and end_token.type != "IDENTIFIER"):
            line_info = f" at line {end_token.line}, column {end_token.col}" if hasattr(end_token, 'line') and hasattr(end_token, 'col') else ""
            raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for range end, got {end_token}{line_info}")
        
        if end_token.type == "IDENTIFIER":
            end = {"type": "identifier", "name": self.advance().value}
        else:
            end = float(self.advance().value)
        
        # Parse step value if present
        by = 1
        if self.match("KEYWORD") and self.tokens[self.pos - 1].value == "by":
            # Check for negative number
            if self.peek() and self.peek().type == "OPERATOR" and self.peek().value == "-":
                self.advance()  # Consume the minus operator
                step_token = self.peek()
                if not step_token or (step_token.type != "NUMBER" and step_token.type != "FLOAT" and step_token.type != "IDENTIFIER"):
                    line_info = f" at line {step_token.line}, column {step_token.col}" if hasattr(step_token, 'line') and hasattr(step_token, 'col') else ""
                    raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for step value, got {step_token}{line_info}")
                
                if step_token.type == "IDENTIFIER":
                    by = {"type": "unary", "operator": "-", "operand": {"type": "identifier", "name": self.advance().value}}
                else:
                    by = -float(self.advance().value)
            else:
                step_token = self.peek()
                if not step_token or (step_token.type != "NUMBER" and step_token.type != "FLOAT" and step_token.type != "IDENTIFIER"):
                    line_info = f" at line {step_token.line}, column {step_token.col}" if hasattr(step_token, 'line') and hasattr(step_token, 'col') else ""
                    raise SyntaxError(f"Expected NUMBER, FLOAT, or IDENTIFIER for step value, got {step_token}{line_info}")
                
                if step_token.type == "IDENTIFIER":
                    by = {"type": "identifier", "name": self.advance().value}
                else:
                    by = float(self.advance().value)
        
        self.expect("PUNCTUATION", "{")
        body = []
        while self.peek() and not (self.peek().type == "PUNCTUATION" and self.peek().value == "}"):
            body.append(self.parse_statement())
        self.expect("PUNCTUATION", "}")
        return {"type": "for", "var": var, "start": start, "end": end, "by": by, "inclusive": is_inclusive, "body": body}

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