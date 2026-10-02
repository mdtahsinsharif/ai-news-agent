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


def update_article_embedding(
    article_id,
    embedding,
):
    """
    Store the embedding generated for an article.
    """

    query = text("""
        UPDATE articles
        SET
            embedding = CAST(
                :embedding AS vector
            )
        WHERE id = :article_id
    """)

    with SessionLocal() as session:

        session.execute(
            query,
            {
                "article_id": article_id,
                "embedding": str(embedding),
            },
        )

        session.commit()


def get_unclustered_articles():
    """
    Get articles that have not been assigned to a story,
    e.g. because embedding failed on a previous run.
    """

    query = (
        select(Article)
        .where(
            ~select(StoryArticle.article_id)
            .where(StoryArticle.article_id == Article.id)
            .exists()
        )
        .order_by(Article.id)
    )

    with SessionLocal() as session:

        return list(session.execute(query).scalars())


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

        # Keep the story active for clustering and the
        # "today" view while it keeps receiving articles.
        story = session.get(Story, story_id)

        story.updated_at = datetime.utcnow()

        session.commit()

from sqlalchemy import text

from database.connection import SessionLocal


def get_story_article_embeddings(story_id):
    """
    Get embeddings for all articles belonging to a story.
    """

    # Use the ORM so pgvector decodes embeddings into
    # arrays; a raw text() query returns them as strings.
    query = (
        select(Article.embedding)
        .join(
            StoryArticle,
            Article.id == StoryArticle.article_id,
        )
        .where(
            StoryArticle.story_id == story_id,
            Article.embedding.is_not(None),
        )
    )

    with SessionLocal() as session:

        return list(
            session.execute(query).scalars()
        )


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
            )
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


