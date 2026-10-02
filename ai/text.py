import html
import re


def clean_text(value):
    """
    Strip HTML tags and entities from feed text.
    """

    value = re.sub(r"<[^>]+>", " ", value or "")

    return re.sub(
        r"\s+",
        " ",
        html.unescape(value),
    ).strip()
