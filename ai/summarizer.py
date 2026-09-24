from google import genai

from database.connection import SessionLocal
from sqlalchemy import text


client = genai.Client()


def get_story_articles(story_id):

    query = text("""
        SELECT
            a.source,
            a.title,
            a.description,
            a.url
        FROM articles a

        JOIN story_articles sa
            ON a.id = sa.article_id

        WHERE sa.story_id = :story_id

        ORDER BY a.published_at DESC
    """)

    with SessionLocal() as session:

        result = session.execute(
            query,
            {
                "story_id": story_id
            },
        )

        return result.mappings().all()


def generate_story_summary(story_id):

    articles = get_story_articles(
        story_id
    )

    if not articles:
        return None

    article_text = "\n\n".join(
        f"""
Source: {article['source']}
Title: {article['title']}
Description: {article['description']}
URL: {article['url']}
"""
        for article in articles
    )

    prompt = f"""
You are a news synthesis assistant.

Multiple news articles below describe the same
underlying story.

Create a concise factual synthesis.

Requirements:

1. Give the story a clear headline.
2. Summarize the key facts.
3. Do not invent information.
4. If sources disagree, explicitly mention
   the disagreement.
5. Preserve source attribution.
6. Keep the summary under 150 words.

Articles:

{article_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text
