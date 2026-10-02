"""
Backfill embeddings for articles saved before the pipeline
stored them, then recompute the centroid of every affected
story.

Usage:
    python backfill_embeddings.py              # all articles
    python backfill_embeddings.py --limit 20   # first 20 only
"""

import argparse
import time

from sqlalchemy import select

from ai.embeddings import (
    generate_embeddings,
    is_daily_quota_error,
)
from ai.story_embedding import refresh_story_embedding
from database.connection import SessionLocal
from database.models import Article, StoryArticle
from database.repository import update_article_embedding


BATCH_SIZE = 100

# The free tier allows 100 embeddings per minute, so on a
# rate-limit error wait out the window and retry the batch.
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 65


def embed_with_retry(texts):

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            return generate_embeddings(texts)

        except Exception as e:

            # The daily quota won't reset for hours, so
            # retrying is pointless.
            if is_daily_quota_error(e) or attempt == MAX_RETRIES:
                raise

            print(
                f"Attempt {attempt} failed "
                f"({str(e)[:80]}), retrying in "
                f"{RETRY_DELAY_SECONDS}s..."
            )

            time.sleep(RETRY_DELAY_SECONDS)


def get_articles_missing_embeddings(limit=None):

    query = (
        select(Article.id, Article.title)
        .where(Article.embedding.is_(None))
        .order_by(Article.id)
    )

    if limit:
        query = query.limit(limit)

    with SessionLocal() as session:

        return session.execute(query).all()


def get_story_ids(article_ids):

    query = (
        select(StoryArticle.story_id)
        .where(StoryArticle.article_id.in_(article_ids))
        .distinct()
    )

    with SessionLocal() as session:

        return list(session.execute(query).scalars())


def backfill(limit=None):

    articles = get_articles_missing_embeddings(limit)

    print(f"Articles missing embeddings: {len(articles)}")

    embedded_ids = []
    failed = 0

    for start in range(0, len(articles), BATCH_SIZE):

        batch = articles[start:start + BATCH_SIZE]

        try:
            embeddings = embed_with_retry(
                [article.title for article in batch]
            )

        except Exception as e:
            print(f"Batch at {start} failed: {e}")
            failed += len(batch)

            if is_daily_quota_error(e):
                print("Daily quota exhausted; rerun later.")
                failed = len(articles) - len(embedded_ids)
                break

            continue

        for article, embedding in zip(batch, embeddings):

            update_article_embedding(
                article_id=article.id,
                embedding=embedding,
            )

            embedded_ids.append(article.id)

        print(f"Embedded {len(embedded_ids)}/{len(articles)}")

    if not embedded_ids:
        print("Nothing embedded.")
        return

    story_ids = get_story_ids(embedded_ids)

    print(f"Refreshing {len(story_ids)} story embeddings...")

    for story_id in story_ids:
        refresh_story_embedding(story_id)

    print("\n====================")
    print(f"Embedded: {len(embedded_ids)}")
    print(f"Failed: {failed}")
    print(f"Stories refreshed: {len(story_ids)}")
    print("====================")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)

    args = parser.parse_args()

    backfill(limit=args.limit)
