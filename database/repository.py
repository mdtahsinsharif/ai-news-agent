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



def get_story_titles(
    story_id,
    limit=3,
):
    """
    Get the most recent article titles in a story.
    """

    query = (
        select(Article.title)
        .join(
            StoryArticle,
            Article.id == StoryArticle.article_id,
        )
        .where(StoryArticle.story_id == story_id)
        .order_by(Article.published_at.desc().nulls_last())
        .limit(limit)
    )

    with SessionLocal() as session:

        return list(session.execute(query).scalars())


def get_merge_candidates(
    min_similarity,
    hours=48,
):
    """
    Find pairs of recent stories whose embeddings are
    similar enough to be duplicates, most similar first.
    Pairs already judged different are excluded.
    """

    query = text("""
        WITH recent AS (
            SELECT
                s.id,
                s.embedding,
                COUNT(sa.article_id) AS article_count
            FROM stories s
            JOIN story_articles sa
                ON s.id = sa.story_id
            WHERE s.embedding IS NOT NULL
              AND s.updated_at >=
                  NOW() - (:hours * INTERVAL '1 hour')
            GROUP BY s.id
        )

        SELECT
            a.id AS story_a,
            b.id AS story_b,
            a.article_count AS count_a,
            b.article_count AS count_b,
            1 - (a.embedding <=> b.embedding) AS similarity

        FROM recent a
        JOIN recent b
            ON a.id < b.id

        WHERE 1 - (a.embedding <=> b.embedding)
              >= :min_similarity

          AND NOT EXISTS (
              SELECT 1
              FROM story_merge_rejections r
              WHERE r.story_a = a.id
                AND r.story_b = b.id
          )

        ORDER BY similarity DESC
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "min_similarity": min_similarity,
                "hours": hours,
            },
        )

        return result.mappings().all()


def merge_stories(
    keep_id,
    drop_id,
):
    """
    Move every article from one story into another and
    delete the emptied story.
    """

    params = {
        "keep_id": keep_id,
        "drop_id": drop_id,
    }

    with SessionLocal() as session:

        session.execute(
            text("""
                UPDATE story_articles
                SET story_id = :keep_id
                WHERE story_id = :drop_id
            """),
            params,
        )

        session.execute(
            text("""
                UPDATE stories k
                SET
                    created_at = LEAST(k.created_at, d.created_at),
                    updated_at = GREATEST(k.updated_at, d.updated_at)
                FROM stories d
                WHERE k.id = :keep_id
                  AND d.id = :drop_id
            """),
            params,
        )

        session.execute(
            text("""
                DELETE FROM stories
                WHERE id = :drop_id
            """),
            params,
        )

        session.commit()


def record_merge_rejection(
    story_a,
    story_b,
):

    query = text("""
        INSERT INTO story_merge_rejections
            (story_a, story_b, checked_at)
        VALUES
            (:story_a, :story_b, NOW())
        ON CONFLICT DO NOTHING
    """)

    with SessionLocal() as session:

        session.execute(
            query,
            {
                "story_a": min(story_a, story_b),
                "story_b": max(story_a, story_b),
            },
        )

        session.commit()
