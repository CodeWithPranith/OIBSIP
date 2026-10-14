from web_chat.emoji_map import replace_shortcodes


def test_known_shortcode_replaced():
    assert replace_shortcodes("hi :smile:") == "hi 😄"


def test_multiple_shortcodes():
    assert replace_shortcodes(":fire::fire: :tada:") == "🔥🔥 🎉"


def test_unknown_shortcode_left_alone():
    assert replace_shortcodes("this :notreal: stays") == "this :notreal: stays"


def test_plain_colons_and_times_untouched():
    assert replace_shortcodes("meet at 10:30: ok") == "meet at 10:30: ok"


def test_plus_one_shortcode():
    assert replace_shortcodes(":+1:") == "👍"
