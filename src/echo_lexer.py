import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line}, col={self.column})"


class Lexer:
    token_patterns = {
        "KEYWORD": r'\b(fn|for|if|else|foreach|in|by|return|break|continue|while|use|mut|watch|type)\b',
        "RETURN_TYPE": r'->',
        "DATATYPE": r'\b(int|float|str|bool|dynamic|list|hash|void)\b',
        "METHOD": r'\b(wait|ask|say|asInt|asFloat|asBool|asString|type|trim|upperCase|lowerCase|length|keys|values|reverse|push|empty|clone|countOf|merge|find|insertAt|pull|removeValue|order|wipe|take|take_last|ensure|pairs|default)\b',
        "BOOLEAN": r'\b(true|false)\b',
        "NULL": r'\bnull\b',
        "FLOAT": r'\b\d+\.\d+\b',
        "NUMBER": r'\b\d+\b',
        "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
        "OPERATOR": r'(==|=>|<=|>=|!=|[=+\-*/%<>]|&&|\|\||!)',
        "RANGE_OPERATOR": r'\.{2,3}',
        "METHOD_OPERATOR": r'\.',  # Separate pattern for method call dot operator
        "PUNCTUATION": r'[(),;:{}\[\]]',  # Removed dot from punctuation
        "STRING": r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'',
        "INTERPOLATION_START": r'\${',
        "INTERPOLATION_END": r'}',
        "WHITESPACE": r'\s+'
    }

    def __init__(self):
        # Compile all regex patterns once to improve performance
        self.compiled_patterns = {k: re.compile(v) for k, v in self.token_patterns.items()}

    def _find_string_end(self, line, start_index, quote_char):
        escaped = False
        idx = start_index + 1
        interp_depth = 0

        while idx < len(line):
            char = line[idx]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif quote_char == '"' and line.startswith("${", idx):
                interp_depth += 1
                idx += 1
            elif interp_depth > 0:
                if char == "{":
                    interp_depth += 1
                elif char == "}":
                    interp_depth -= 1
            elif char == quote_char:
                return idx
            idx += 1
        return -1

    def _tokenize_interpolation_expr(self, expr_content, line_number, base_column):
        parts = []
        expr_pos = 0

        while expr_pos < len(expr_content):
            if expr_content[expr_pos].isspace():
                expr_pos += 1
                continue

            expr_match = None
            for token_type, regex in self.compiled_patterns.items():
                expr_match = regex.match(expr_content, expr_pos)
                if expr_match:
                    token_value = expr_match.group(0)
                    parts.append(Token(token_type, token_value, line_number, base_column + expr_pos))
                    expr_pos = expr_match.end()
                    break

            if not expr_match:
                expr_pos += 1

        return parts

    def read_source(self, src_file):
        tokens = []
        in_multiline_comment = False
        
        with open(src_file, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, start=1):
                line = line.rstrip('\n')
                position = 0
                
                while position < len(line):
                    # Skip whitespace
                    if line[position].isspace():
                        position += 1
                        continue
                    
                    # Handle single-line comments
                    if line.startswith("//", position):
                        break  # Ignore the rest of the line
                    
                    # Handle multi-line comments
                    if line.startswith("/*", position):
                        in_multiline_comment = True
                        position += 2
                        continue
                    if in_multiline_comment:
                        if "*/" in line[position:]:
                            in_multiline_comment = False
                            position = line.index("*/", position) + 2
                        else:
                            break  # Continue to the next line
                        continue
                    
                    # Handle string interpolation
                    if line[position] == '"' or line[position] == "'":
                        quote_char = line[position]
                        # Find the end of the string
                        end_quote = self._find_string_end(line, position, quote_char)
                        if end_quote == -1:
                            raise SyntaxError(
                                f"Unterminated string at line {line_number}, column {position + 1}. "
                                f"Did you forget a closing '{quote_char}'?"
                            )

                        
                        # Check for string interpolation
                        string_content = line[position:end_quote + 1]
                        if "${" in string_content and "}" in string_content:
                            # Handle string interpolation
                            parts = []
                            current_pos = position + 1
                            
                            while current_pos < end_quote:
                                # Find the next interpolation
                                start_interp = line.find("${", current_pos)
                                if start_interp == -1 or start_interp >= end_quote:
                                    # No more interpolations, add the rest of the string
                                    if current_pos < end_quote:
                                        parts.append(Token("STRING", line[current_pos:end_quote], line_number, current_pos + 1))
                                    break
                                
                                # Add the string before the interpolation
                                if start_interp > current_pos:
                                    parts.append(Token("STRING", line[current_pos:start_interp], line_number, current_pos + 1))
                                
                                # Add the interpolation start token
                                parts.append(Token("INTERPOLATION_START", "${", line_number, start_interp + 1))
                                
                                # Find the end of the interpolation
                                end_interp = line.find("}", start_interp)
                                if end_interp == -1 or end_interp >= end_quote:
                                    raise SyntaxError(
                                        f"Missing closing brace in string interpolation at line {line_number}, "
                                        f"column {start_interp + 1}."
                                    )
                                
                                # Tokenize the expression inside interpolation
                                expr_content = line[start_interp + 2:end_interp]
                                parts.extend(self._tokenize_interpolation_expr(expr_content, line_number, start_interp + 2))
                                
                                # Add the interpolation end token
                                parts.append(Token("INTERPOLATION_END", "}", line_number, end_interp + 1))
                                
                                current_pos = end_interp + 1
                            
                            # Add all parts to the tokens list
                            tokens.extend(parts)
                            position = end_quote + 1
                            continue
                        else:
                            # Regular string, no interpolation
                            tokens.append(Token("STRING", string_content, line_number, position + 1))
                            position = end_quote + 1
                            continue
                    
                    match = None
                    for token_type, regex in self.compiled_patterns.items():
                        match = regex.match(line, position)
                        if match:
                            token_value = match.group(0)
                            tokens.append(Token(token_type, token_value, line_number, position + 1))
                            position = match.end()
                            break
                    
                    if not match:
                        # Capture all consecutive invalid characters
                        invalid_match = re.match(r'\S+', line[position:])
                        if not invalid_match:
                            position += 1
                            continue
                        invalid_sequence = invalid_match.group(0)
                        context = line[max(0, position - 10):position + 10]
                        raise SyntaxError(
                            f"Invalid token '{invalid_sequence}' at line {line_number}, column {position + 1}. "
                            f"Check for unsupported characters or typos. Context: '{context}'"
                        )

        # print(tokens)
        return tokens

