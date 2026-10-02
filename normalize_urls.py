"""
One-off migration: strip tracking parameters from stored
article URLs so they match what the pipeline now saves.

Usage:
    python normalize_urls.py --dry-run
    python normalize_urls.py
"""

import argparse

from sqlalchemy import select, update

from database.connection import SessionLocal
from database.models import Article
from ingestion.dedup import normalize_url


def normalize_stored_urls(dry_run=False):

    with SessionLocal() as session:

        articles = session.execute(
            select(Article.id, Article.url)
        ).all()

        existing = {url for _, url in articles}

        changes = []
        collisions = []

        for article_id, url in articles:

            normalized = normalize_url(url)

            if normalized == url:
                continue

            # Another row already has this URL (or will):
            # leave it rather than break the unique index.
            if normalized in existing:
                collisions.append((article_id, url))
                continue

            existing.add(normalized)
            changes.append((article_id, normalized))

        print(f"URLs to normalize: {len(changes)}")
        print(f"Skipped (would duplicate): {len(collisions)}")

        for article_id, url in collisions[:10]:
            print(f"  {article_id}: {url}")

        if dry_run:
            return

        for article_id, normalized in changes:

            session.execute(
                update(Article)
                .where(Article.id == article_id)
                .values(url=normalized)
            )

        session.commit()

        print("Done.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    normalize_stored_urls(dry_run=args.dry_run)
