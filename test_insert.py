from database.repository import save_article

article = save_article({
    "source": "TEST",
    "title": "Test article",
    "url": "https://example.com/test-123",
    "description": "Test description",
})

print(article.id)