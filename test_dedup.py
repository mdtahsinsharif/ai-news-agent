from ingestion.article_service import (
    save_article_if_new,
)


article = {
    "source": "TestSource",
    "title": "Duplicate test article",
    "url": "https://test.example.com/duplicate-test",
    "category": "Technology",
}


first = save_article_if_new(article)

print(
    "First result:",
    first.id if first else None
)


second = save_article_if_new(article)

print(
    "Second result:",
    second.id if second else None
)
