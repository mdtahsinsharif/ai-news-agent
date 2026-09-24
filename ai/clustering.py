from database.repository import (
    find_similar_stories,
    create_story,
    attach_article_to_story,
)

from ai.story_embedding import refresh_story_embedding


SIMILARITY_THRESHOLD = 0.80


def assign_article_to_story(
    article,
    embedding,
    threshold=SIMILARITY_THRESHOLD,
):

    similar_stories = find_similar_stories(
        embedding=embedding,
        limit=5,
    )

    if not similar_stories:

        story = create_story(
            article=article,
            embedding=embedding,
        )

        return {
            "action": "created",
            "story_id": story.id,
            "similarity": None,
        }

    best_story = similar_stories[0]

    similarity = float(
        best_story["similarity"]
    )

    if similarity >= threshold:

        attach_article_to_story(
            article_id=article["id"],
            story_id=best_story["id"],
            similarity=similarity,
        )

        return {
            "action": "attached",
            "story_id": best_story["id"],
            "similarity": similarity,
        }

    story = create_story(
        article=article,
        embedding=embedding,
    )

    return {
        "action": "created",
        "story_id": story.id,
        "similarity": similarity,
    }