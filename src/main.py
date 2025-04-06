from neura_lexer import Lexer
from neura_parser import Parser
from neura_interpreter import Interpreter

# BUG: need to fix default()
# TODO: need to fix comments highlighting
# BUG: need to check notify() issue
# TODO: need to add type check/hint in func definition
# TODO: cmd line tool to run the src code

if __name__ == "__main__":
    lex_obj = Lexer()
    tokens = lex_obj.read_source(r".\source.neu")
    # print("Tokens from lexer:", tokens)

    parser_obj = Parser(tokens)
    try:
        ast = parser_obj.parse()
        # print("\nAbstract Syntax Tree:")
        # print(ast)

        interpreter = Interpreter()
        interpreter.execute(ast)

    except SyntaxError as e:
        print(f"\nSyntax Error: {e}")
