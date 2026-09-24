import feedparser
from datetime import datetime
import hashlib

def fetch_feed(source_name: str, url: str, category: str):

    feed = feedparser.parse(url)

    articles = []

    for entry in feed.entries:

        articles.append({
            "source": source_name,
            "title": entry.get("title"),
            "url": entry.get("link"),
            "description": entry.get("summary"),
            "author": entry.get("author"),
            "published_at": parse_date(
                entry.get("published_parsed")),
            "category": category,
        })

    return articles


def parse_date(value):
    if not value:
        return None
    return datetime(*value[:6])

def normalize_article(article):
    return {
        "source": article["source"].strip(),
        "title": article["title"].strip(),
        "url": article["url"].strip(),
        "description": (
            article.get("description") or ""
        ).strip(),
        "author": article.get("author"),
        "published_at": article.get("published_at")
    }

def normalize_url(url):
    return url.split("?")[0].rstrip("/")

def title_hash(title):
    normalized = title.lower().strip()
    return hashlib.sha256(
        normalized.encode()
    ).hexdigest()

def get_unique_articles(articles):
    seen = set()

    unique_articles = []

    for article in articles:

        url = normalize_url(article["url"])

        if url in seen:
            continue

        seen.add(url)

        unique_articles.append(article)

    return unique_articles