from ingestion.fetch_all import (
    fetch_all_sources,
)

from ingestion.article_service import (
    save_article_if_new,
)

from ai.embeddings import (
    generate_embedding,
    is_daily_quota_error,
)

from database.repository import (
    get_unclustered_articles,
    update_article_embedding,
)

from ai.clustering import (
    assign_article_to_story,
)


def cluster_article(article):

    # ---------------------------------------------
    # Generate embedding (reuse one saved earlier)
    # ---------------------------------------------

    if article.embedding is None:

        embedding = generate_embedding(
            article.title
        )

        update_article_embedding(
            article_id=article.id,
            embedding=embedding,
        )

    else:

        embedding = [
            float(value)
            for value in article.embedding
        ]

    # ---------------------------------------------
    # Cluster
    # ---------------------------------------------

    clustering_article = {
        "id": article.id,
        "title": article.title,
        "category": article.category,
    }

    return assign_article_to_story(
        article=clustering_article,
        embedding=embedding,
    )


def process_news():

    articles = fetch_all_sources()

    print(
        f"\nFetched {len(articles)} articles"
    )

    # ---------------------------------------------
    # Save only new articles
    # ---------------------------------------------

    saved = 0
    skipped = 0

    for article_data in articles:

        article = save_article_if_new(
            article_data
        )

        if article is None:

            skipped += 1

            continue

        saved += 1

    # ---------------------------------------------
    # Cluster every article without a story,
    # including ones left over from failed runs
    # ---------------------------------------------

    pending = get_unclustered_articles()

    print(
        f"\nArticles to cluster: {len(pending)}"
    )

    processed = 0
    failed = 0

    for article in pending:

        try:

            result = cluster_article(article)

        except Exception as e:

            if is_daily_quota_error(e):

                print(
                    "\nDaily embedding quota exhausted; "
                    "remaining articles will be "
                    "clustered on the next run."
                )

                break

            print(
                f"\nFailed to cluster article "
                f"{article.id}: {e}"
            )

            failed += 1

            continue

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
        f"Saved: {saved}"
    )

    print(
        f"Skipped: {skipped}"
    )

    print(
        f"Clustered: {processed}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Remaining: {len(pending) - processed - failed}"
    )

    print("====================")
