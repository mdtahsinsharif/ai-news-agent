from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


# Query parameters feeds add for analytics; they don't change
# which article the URL points to.
TRACKING_PARAMS = {
    "traffic_source",
    "cmpid",
    "ocid",
    "fbclid",
    "gclid",
    "ref",
    "maca",
}

TRACKING_PREFIXES = (
    "utm_",
    "at_",
)


def is_tracking_param(key):

    key = key.lower()

    return (
        key in TRACKING_PARAMS
        or key.startswith(TRACKING_PREFIXES)
    )


def normalize_url(url):
    """
    Strip tracking parameters and fragments so the same
    article shared with different tags is stored once.
    """

    parts = urlsplit(url.strip())

    query = [
        (key, value)
        for key, value in parse_qsl(
            parts.query,
            keep_blank_values=True,
        )
        if not is_tracking_param(key)
    ]

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query),
        "",
    ))


def deduplicate_articles(articles):

    seen = set()

    unique = []

    for article in articles:

        url = normalize_url(
            article["url"]
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        unique.append(article)

    return unique
