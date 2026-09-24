from ai.embeddings import generate_embedding
from ai.clustering import assign_article_to_story

from database.repository import save_article


articles = [
    {
        "source": "TestSource",
        "title": "OpenAI announces a new AI model",
        "url": "https://test.example.com/openai-new-model",
        "category": "Technology",
    },
    {
        "source": "TestSource",
        "title": "OpenAI launches its latest artificial intelligence model",
        "url": "https://test.example.com/openai-latest-model",
        "category": "Technology",
    },
    {
        "source": "TestSource",
        "title": "Toronto Maple Leafs win their hockey game",
        "url": "https://test.example.com/maple-leafs-win",
        "category": "Sports",
    },
]


for article_data in articles:

    # --------------------------------------------------
    # 1. Save the article to PostgreSQL
    # --------------------------------------------------

    article = save_article(article_data)

    print(f"\nSaved article ID: {article.id}")

    # --------------------------------------------------
    # 2. Generate embedding
    # --------------------------------------------------

    embedding = generate_embedding(article.title)

    # --------------------------------------------------
    # 3. Build the article object used by clustering
    #
    # IMPORTANT:
    # Use article.id returned by PostgreSQL.
    # Do NOT use a manually assigned ID.
    # --------------------------------------------------

    article_for_clustering = {
        "id": article.id,
        "title": article.title,
        "category": article.category,
    }

    # --------------------------------------------------
    # 4. Assign article to a story
    # --------------------------------------------------

    result = assign_article_to_story(
        article=article_for_clustering,
        embedding=embedding,
    )

    # --------------------------------------------------
    # 5. Print result
    # --------------------------------------------------

    print(
        f"Article: {article.title}"
    )

    print(
        f"Action: {result['action']}"
    )

    print(
        f"Story: {result['story_id']}"
    )

    print(
        f"Similarity: {result['similarity']}"
    )
