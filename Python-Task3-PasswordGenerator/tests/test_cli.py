from password_app.cli import run_cli


def make_input(answers):
    iterator = iter(answers)
    return lambda _prompt="": next(iterator)


def test_cli_generates_then_quits(capsys):
    answers = ["12", "y", "y", "y", "y", "n"]
    run_cli(make_input(answers))
    output = capsys.readouterr().out
    assert "Your password:" in output
    assert "Goodbye" in output


def test_cli_rejects_short_length_then_allows_retry(capsys):
    # first round: length 4 -> error; then "y" to try again; second round valid
    answers = ["4", "y", "y", "y", "y", "y", "10", "y", "y", "y", "y", "n"]
    run_cli(make_input(answers))
    output = capsys.readouterr().out
    assert "at least 8" in output
    assert "Your password:" in output


def test_cli_rejects_single_type(capsys):
    answers = ["12", "y", "n", "n", "n", "n"]
    run_cli(make_input(answers))
    assert "at least 2" in capsys.readouterr().out


def test_cli_reprompts_on_bad_yes_no(capsys):
    answers = ["12", "maybe", "y", "y", "y", "y", "n"]
    run_cli(make_input(answers))
    assert "Please answer y or n" in capsys.readouterr().out
