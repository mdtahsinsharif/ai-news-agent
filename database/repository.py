from datetime import datetime

from sqlalchemy import select, text

from database.connection import SessionLocal
from database.models import (
    Article,
    Story,
    StoryArticle,
)


# ============================================================
# ARTICLE FUNCTIONS
# ============================================================

def article_exists(url):
    """
    Check whether an article already exists based on its URL.
    """

    with SessionLocal() as session:

        result = session.execute(
            select(Article).where(
                Article.url == url
            )
        )

        return result.scalar_one_or_none() is not None


def save_article(data):
    """
    Save an article to the articles table.
    """

    with SessionLocal() as session:

        article = Article(**data)

        session.add(article)

        session.commit()

        session.refresh(article)

        return article


# ============================================================
# STORY FUNCTIONS
# ============================================================

def find_similar_stories1(
    embedding,
    limit=10,
):
    """
    Find existing stories whose embeddings are
    semantically similar to the supplied embedding.
    """

    query = text("""
        SELECT
            id,
            headline,
            summary,
            category,

            1 - (
                embedding <=> CAST(
                    :embedding AS vector
                )
            ) AS similarity

        FROM stories

        WHERE embedding IS NOT NULL

        ORDER BY
            embedding <=> CAST(
                :embedding AS vector
            )

        LIMIT :limit
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "embedding": str(embedding),
                "limit": limit,
            },
        )

        return result.mappings().all()

def find_similar_stories(
    embedding,
    limit=10,
    hours=48,
):
    """
    Find semantically similar stories updated
    within the specified time window.
    """

    query = text("""
        SELECT
            id,
            headline,
            summary,
            category,

            1 - (
                embedding <=> CAST(
                    :embedding AS vector
                )
            ) AS similarity

        FROM stories

        WHERE embedding IS NOT NULL

          AND updated_at >=
              NOW() - (
                  :hours * INTERVAL '1 hour'
              )

        ORDER BY
            embedding <=> CAST(
                :embedding AS vector
            )

        LIMIT :limit
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "embedding": str(embedding),
                "limit": limit,
                "hours": hours,
            },
        )

        return result.mappings().all()


def create_story(
    article,
    embedding,
):
    """
    Create a new story and attach the article
    that created the story.
    """

    with SessionLocal() as session:

        story = Story(
            headline=article["title"],
            summary=None,
            category=article.get("category"),
            importance=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            embedding=embedding,
        )

        session.add(story)

        # Get the generated story ID.
        session.flush()

        relationship = StoryArticle(
            story_id=story.id,
            article_id=article["id"],
            similarity=1.0,
        )

        session.add(relationship)

        session.commit()

        session.refresh(story)

        return story


def attach_article_to_story(
    article_id,
    story_id,
    similarity,
):
    """
    Attach an existing article to an existing story.
    """

    with SessionLocal() as session:

        relationship = StoryArticle(
            story_id=story_id,
            article_id=article_id,
            similarity=similarity,
        )

        session.add(relationship)

        session.commit()

from sqlalchemy import text

from database.connection import SessionLocal


def get_story_article_embeddings(story_id):
    """
    Get embeddings for all articles belonging to a story.
    """

    query = text("""
        SELECT
            a.embedding
        FROM articles a
        JOIN story_articles sa
            ON a.id = sa.article_id
        WHERE sa.story_id = :story_id
          AND a.embedding IS NOT NULL
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "story_id": story_id,
            },
        )

        return [
            row[0]
            for row in result.fetchall()
        ]


def update_story_embedding(
    story_id,
    embedding,
):
    """
    Update the embedding stored for a story.
    """

    query = text("""
        UPDATE stories
        SET
            embedding = CAST(
                :embedding AS vector
            ),
            updated_at = NOW()
        WHERE id = :story_id
    """)

    with SessionLocal() as session:

        session.execute(
            query,
            {
                "story_id": story_id,
                "embedding": str(embedding),
            },
        )

        session.commit()

def update_story_summary(
    story_id,
    headline,
    summary,
):
    query = text("""
        UPDATE stories
        SET
            headline = :headline,
            summary = :summary,
            updated_at = NOW()
        WHERE id = :story_id
    """)

    with SessionLocal() as session:

        session.execute(
            query,
            {
                "story_id": story_id,
                "headline": headline,
                "summary": summary,
            },
        )

        session.commit()


