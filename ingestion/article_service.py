from database.repository import (
    article_exists,
    save_article,
)


def save_article_if_new(article_data):
    """
    Save an article only if its URL has not
    already been stored.
    """

    url = article_data["url"]

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
