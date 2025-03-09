import re

class Lexer:
    token_patterns = {
        "KEYWORD": r'\b(fn|for|if|else|foreach|in|by|return|break|continue)\b',
        "DATATYPE": r'\b(int|float|str|bool|dynamic|list|hash)\b',
        "METHOD": r'\b(notify|wait|ask|say|asInt|asFloat|asBool|trim|uppercase|lowercase|length)\b',
        "BOOLEAN": r'\b(true|false)\b',
        "NUMBER": r'\b\d+\b',
        "IDENTIFIER": r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
        "OPERATOR": r'(==|=>|<=|>=|!=|[=+\-*/<>])',
        "PUNCTUATION": r'[(),.;:{}\[\]]',
        "STRING": r'"[^"]*"',
        "WHITESPACE": r'\s+'
    }

    def __init__(self):
        # Compile all regex patterns once to improve performance
        self.compiled_patterns = {k: re.compile(v) for k, v in self.token_patterns.items()}
        print(self.compiled_patterns)

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
                    
                    match = None
                    for token_type, regex in self.compiled_patterns.items():
                        match = regex.match(line, position)
                        if match:
                            token_value = match.group(0)
                            tokens.append(f"{token_type}({token_value})")
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

        print(tokens)

if __name__ == "__main__":
    lex_obj = Lexer()
    lex_obj.read_source(r"C:\Users\Deekshith\Desktop\Neura\my_source.neu")
