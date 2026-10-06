from datetime import datetime, timedelta

from ingestion.dedup import normalize_url

from database.repository import (
    article_exists,
    save_article,
)


# Some feeds include items that are years old; they would
# otherwise start fresh stories and show up as today's news.
MAX_ARTICLE_AGE = timedelta(days=3)


def save_article_if_new(article_data):
    """
    Save an article only if its URL has not
    already been stored.
    """

    url = article_data.get("url")

    if not url or not article_data.get("title"):

        print(
            f"Skipping entry without URL or title: {url}"
        )

        return None

    published_at = article_data.get("published_at")

    # Feed dates are parsed as UTC; entries without a date
    # are kept since their age is unknown.
    if (
        published_at is not None
        and published_at < datetime.utcnow() - MAX_ARTICLE_AGE
    ):

        print(
            f"Skipping old article ({published_at:%Y-%m-%d}): {url}"
        )

        return None

    url = normalize_url(url)

    article_data = {
        **article_data,
        "url": url,
    }

    if article_exists(url):

        print(
            f"Already exists: {url}"
        )

        return None

    article = save_article(
        article_data
    )

    print(
        f"Saved article {article.id}: "
        f"{article.title}"
    )

    return article
