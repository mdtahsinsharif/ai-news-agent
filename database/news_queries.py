from sqlalchemy import text

from database.connection import SessionLocal


def get_todays_stories():

    query = text("""
        SELECT
            s.id,
            s.headline,
            s.summary,
            s.category,
            s.importance,
            s.created_at,
            s.updated_at,

            COUNT(sa.article_id)
                AS article_count

        FROM stories s

        JOIN story_articles sa
            ON s.id = sa.story_id

        WHERE s.updated_at >= CURRENT_DATE

        GROUP BY
            s.id

        ORDER BY
            s.updated_at DESC
    """)

    with SessionLocal() as session:

        result = session.execute(query)

        return result.mappings().all()

def get_story_articles(story_id):

    query = text("""
        SELECT
            a.id,
            a.source,
            a.title,
            a.url,
            a.author,
            a.published_at

        FROM articles a

        JOIN story_articles sa
            ON a.id = sa.article_id

        WHERE sa.story_id = :story_id

        ORDER BY
            a.published_at DESC
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "story_id": story_id,
            },
        )

        return result.mappings().all()

