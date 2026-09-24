from ingestion.normalizer import normalize_article


article = {
    "source": "  BBC  ",
    "title": "  Test headline  ",
    "url": " https://example.com/test ",
    "description": None,
    "author": None,
    "published_at": None
}


result = normalize_article(article)

print(result)