"""
Embed articles and recompute the centroid of every affected
story.

Clustering only compares against stories updated in the last
48 hours, so after changing how embeddings are built only
that window needs re-embedding; older stories are never
compared again.

Usage:
    # Re-embed every article in recently active stories
    python backfill_embeddings.py --hours 48

    # Embed articles that have no embedding at all
    python backfill_embeddings.py

    # Show what would be embedded without calling Gemini
    python backfill_embeddings.py --hours 48 --dry-run

    --limit N processes only the first N articles.
"""

import argparse
import time
from datetime import timedelta

from sqlalchemy import func, select

from ai.embeddings import (
    build_embedding_text,
    generate_embeddings,
    is_daily_quota_error,
)
from ai.story_embedding import refresh_story_embedding
from database.connection import SessionLocal
from database.models import Article, Story, StoryArticle
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


def get_articles_to_embed(hours=None, limit=None):
    """
    With hours: every article in a story updated within that
    window, including ones already embedded. Without: every
    article that has no embedding.
    """

    query = (
        select(Article.id, Article.title, Article.description)
        .order_by(Article.id)
    )

    if hours:

        recent_story_articles = (
            select(StoryArticle.article_id)
            .join(Story, Story.id == StoryArticle.story_id)
            .where(
                Story.updated_at
                >= func.now() - timedelta(hours=hours)
            )
        )

        query = query.where(
            Article.id.in_(recent_story_articles)
        )

    else:

        query = query.where(Article.embedding.is_(None))

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


def backfill(hours=None, limit=None, dry_run=False):

    articles = get_articles_to_embed(hours, limit)

    print(f"Articles to embed: {len(articles)}")

    if dry_run:

        for article in articles[:3]:
            print("\n---")
            print(build_embedding_text(article.title, article.description))

        return

    embedded_ids = []
    failed = 0

    for start in range(0, len(articles), BATCH_SIZE):

        batch = articles[start:start + BATCH_SIZE]

        try:
            embeddings = embed_with_retry([
                build_embedding_text(
                    article.title,
                    article.description,
                )
                for article in batch
            ])

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
    parser.add_argument("--hours", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    backfill(
        hours=args.hours,
        limit=args.limit,
        dry_run=args.dry_run,
    )
