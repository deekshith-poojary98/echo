from echo_lexer import Lexer
from echo_parser import Parser
from echo_interpreter import Interpreter


# TODO: need to fix comments highlighting
# TODO: cmd line tool to run the src code

if __name__ == "__main__":
    lex_obj = Lexer()
    tokens = lex_obj.read_source(r".\syntaxes\source.echo")
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
