def normalize_url(url):

    return (
        url
        .split("?")[0]
        .rstrip("/")
    )


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