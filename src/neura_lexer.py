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
        "KEYWORD": r'\b(fn|for|if|else|foreach|in|by|return|break|continue|while)\b',
        "RETURN_TYPE": r'->',
        "DATATYPE": r'\b(int|float|str|bool|dynamic|list|hash|void)\b',
        "METHOD": r'\b(wait|ask|say|asInt|asFloat|asBool|asString|type|trim|upperCase|lowerCase|length|keys|values|reverse|push|empty|clone|countOf|merge|find|insertAt|pull|removeValue|order)\b',
        "BOOLEAN": r'\b(true|false)\b',
        "FLOAT": r'\b\d+\.\d+\b',
        "NUMBER": r'\b\d+\b',
        "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
        "OPERATOR": r'(==|=>|<=|>=|!=|[=+\-*/%<>]|&&|\|\||!)',
        "RANGE_OPERATOR": r'\.{2,3}',
        "METHOD_OPERATOR": r'\.',  # Separate pattern for method call dot operator
        "PUNCTUATION": r'[(),;:{}\[\]]',  # Removed dot from punctuation
        "STRING": r'"[^"]*"',
        "INTERPOLATION_START": r'\${',
        "INTERPOLATION_END": r'}',
        "WHITESPACE": r'\s+'
    }

    def __init__(self):
        # Compile all regex patterns once to improve performance
        self.compiled_patterns = {k: re.compile(v) for k, v in self.token_patterns.items()}

    def read_source(self, src_file):
        tokens = []
        in_multiline_comment = False
        
        with open(src_file, 'r') as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
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
                    if line[position] == '"':
                        # Find the end of the string
                        end_quote = line.find('"', position + 1)
                        if end_quote == -1:
                            print(f"Error: Unterminated string at line {line_number}, position {position + 1}.")
                            break
                        
                        # Check for string interpolation
                        string_content = line[position:end_quote + 1]
                        if "${" in string_content and "}" in string_content:
                            # Handle string interpolation
                            parts = []
                            current_pos = position + 1  # Skip the opening quote
                            
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
                                
                                # Find the end of the interpolation
                                end_interp = line.find("}", start_interp)
                                if end_interp == -1 or end_interp >= end_quote:
                                    print(f"Error: Missing closing brace in string interpolation at line {line_number}, position {start_interp + 1}.")
                                    break
                                
                                # Add the interpolation start token
                                parts.append(Token("INTERPOLATION_START", "${", line_number, start_interp + 1))
                                
                                # Extract the variable name
                                var_name = line[start_interp + 2:end_interp]
                                parts.append(Token("IDENTIFIER", var_name, line_number, start_interp + 3))
                                
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
                            if token_type == "STRING":
                                print(f"Found string token: {token_value}")
                            tokens.append(Token(token_type, token_value, line_number, position + 1))
                            position = match.end()
                            break
                    
                    if not match:
                        # Capture all consecutive invalid characters
                        invalid_sequence = re.match(r'\S+', line[position:]).group(0)
                        print(f"Error: Invalid token '{invalid_sequence}' at line {line_number}, position {position + 1}.")
                        print(f"Line {line_number}: {line}")
                        print(" " * (position + 7) + "^")
                        print(f"Hint: Check for unsupported characters or typos. Context: '{line[max(0, position-10):position+10]}'\n")
                        
                        # Skip the entire invalid sequence to avoid repetitive errors
                        position += len(invalid_sequence)

        # print(tokens)
        return tokens

