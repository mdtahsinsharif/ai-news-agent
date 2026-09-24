def normalize_article(article):

    return {
        "source": (
            article.get("source") or ""
        ).strip(),

        "title": (
            article.get("title") or ""
        ).strip(),

        "url": (
            article.get("url") or ""
        ).strip(),

        "description": (
            article.get("description") or ""
        ).strip(),

        "author": article.get("author"),

        "published_at": article.get(
            "published_at"
        )
    }