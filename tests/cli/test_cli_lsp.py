from echo.cli.main import main


def test_lsp_help_exits_zero():
    # argparse -h raises SystemExit(0)
    try:
        main(["lsp", "-h"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("expected SystemExit from -h")
