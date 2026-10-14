"""Turn emoji shortcodes such as :smile: into Unicode characters."""

import re

EMOJI = {
    "smile": "😄", "grin": "😁", "joy": "😂", "laughing": "😆", "wink": "😉",
    "blush": "😊", "heart_eyes": "😍", "kiss": "😘", "sunglasses": "😎",
    "thinking": "🤔", "neutral": "😐", "unamused": "😒", "sob": "😭", "cry": "😢",
    "angry": "😠", "scream": "😱", "sleeping": "😴", "wave": "👋", "ok_hand": "👌",
    "thumbsup": "👍", "+1": "👍", "thumbsdown": "👎", "-1": "👎", "clap": "👏",
    "pray": "🙏", "muscle": "💪", "heart": "❤️", "broken_heart": "💔", "fire": "🔥",
    "star": "⭐", "sparkles": "✨", "tada": "🎉", "party": "🥳", "100": "💯",
    "rocket": "🚀", "check": "✅", "x": "❌", "warning": "⚠️", "eyes": "👀",
    "coffee": "☕", "pizza": "🍕", "sun": "☀️", "moon": "🌙", "bulb": "💡",
}

_SHORTCODE = re.compile(r":([a-z0-9_+-]+):")


def replace_shortcodes(text):
    """Replace known :shortcodes:; unknown ones are left exactly as typed."""
    return _SHORTCODE.sub(lambda m: EMOJI.get(m.group(1), m.group(0)), text)
