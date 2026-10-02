from ingestion.fetch_all import (
    fetch_all_sources,
)

from ingestion.article_service import (
    save_article_if_new,
)

from ai.embeddings import (
    generate_embedding,
)

from database.repository import (
    update_article_embedding,
)

from ai.clustering import (
    assign_article_to_story,
)


def process_news():

    articles = fetch_all_sources()

    print(
        f"\nFetched {len(articles)} articles"
    )

    processed = 0
    skipped = 0

    for article_data in articles:

        # ---------------------------------------------
        # Save only new articles
        # ---------------------------------------------

        article = save_article_if_new(
            article_data
        )

        if article is None:

            skipped += 1

            continue

        # ---------------------------------------------
        # Generate embedding
        # ---------------------------------------------

        embedding = generate_embedding(
            article.title
        )

        update_article_embedding(
            article_id=article.id,
            embedding=embedding,
        )

        # ---------------------------------------------
        # Cluster
        # ---------------------------------------------

        clustering_article = {
            "id": article.id,
            "title": article.title,
            "category": article.category,
        }

        result = assign_article_to_story(
            article=clustering_article,
            embedding=embedding,
        )

        print(
            f"\n{article.title}"
        )

        print(
            f"→ {result['action']}"
        )

        print(
            f"→ Story {result['story_id']}"
        )

        print(
            f"→ Similarity {result['similarity']}"
        )

        processed += 1

    print("\n====================")

    print(
        f"Processed: {processed}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print("====================")