import pytest

from password_app import generator as g


def test_length_is_respected():
    for length in (8, 12, 33, 64):
        assert len(g.generate_password(length)) == length


def test_contains_at_least_one_of_each_selected_type():
    # Repeat many times: a random-only approach would fail this sometimes.
    for _ in range(500):
        pw = g.generate_password(8)
        assert any(c in g.UPPERCASE for c in pw)
        assert any(c in g.LOWERCASE for c in pw)
        assert any(c in g.DIGITS for c in pw)
        assert any(c in g.SYMBOLS for c in pw)


def test_only_selected_types_are_used():
    for _ in range(200):
        pw = g.generate_password(20, use_upper=False, use_lower=True, use_digits=True, use_symbols=False)
        assert all(c in g.LOWERCASE + g.DIGITS for c in pw)
        assert any(c in g.LOWERCASE for c in pw) and any(c in g.DIGITS for c in pw)


def test_excludes_ambiguous_characters():
    for _ in range(300):
        pw = g.generate_password(40, exclude_ambiguous=True)
        assert not any(c in g.AMBIGUOUS for c in pw)


@pytest.mark.parametrize("bad_length", [7, 0, -5, 65, 1000])
def test_out_of_range_length_rejected(bad_length):
    with pytest.raises(g.PasswordConfigError):
        g.generate_password(bad_length)


@pytest.mark.parametrize("bad_length", ["abc", "", None, "8.5", True])
def test_non_integer_length_rejected(bad_length):
    with pytest.raises(g.PasswordConfigError):
        g.generate_password(bad_length)


def test_string_length_is_accepted():
    assert len(g.generate_password("12")) == 12


def test_fewer_than_two_types_rejected():
    with pytest.raises(g.PasswordConfigError):
        g.generate_password(12, False, False, False, False)
    with pytest.raises(g.PasswordConfigError):
        g.generate_password(12, True, False, False, False)


def test_passwords_are_not_repeated():
    assert len({g.generate_password(16) for _ in range(200)}) == 200


def test_uses_secrets_not_random():
    import inspect
    source = inspect.getsource(g)
    assert "import secrets" in source
    assert "import random" not in source


@pytest.mark.parametrize(
    "password, expected",
    [("abcdefgh", "Weak"), ("abcd1234", "Weak"), ("Abcdef1234", "Medium"), ("Tr0ub4dor&3xK!9zQ#", "Strong")],
)
def test_strength_labels(password, expected):
    assert g.estimate_strength(password)[0] == expected


def test_strength_of_empty_password():
    assert g.estimate_strength("")[0] == "Weak"


def test_longer_passwords_are_rated_at_least_as_strong():
    ranks = {"Weak": 0, "Medium": 1, "Strong": 2}
    short = ranks[g.estimate_strength(g.generate_password(8))[0]]
    long = ranks[g.estimate_strength(g.generate_password(30))[0]]
    assert long >= short


def test_history_keeps_only_last_five_newest_first():
    history = g.PasswordHistory()
    for i in range(8):
        history.add(f"pw{i}")
    assert history.items() == ["pw7", "pw6", "pw5", "pw4", "pw3"]
