from database.repository import (
    find_similar_stories,
    create_story,
    attach_article_to_story,
)

from ai.same_story import (
    describe_article,
    describe_story,
)

from ai.story_embedding import refresh_story_embedding


# Above this, the article is attached without asking the LLM.
AUTO_ATTACH_THRESHOLD = 0.85

# Below this, the article always starts a new story.
CANDIDATE_THRESHOLD = 0.72

# Used in the gray zone when the LLM can't be asked.
FALLBACK_THRESHOLD = 0.80


def should_attach(article, story, similarity, checker):

    if similarity >= AUTO_ATTACH_THRESHOLD:
        return True

    if similarity < CANDIDATE_THRESHOLD:
        return False

    verdict = None

    if checker is not None:

        verdict = checker.check(
            describe_article(article),
            describe_story(story["id"]),
        )

    if verdict is None:
        return similarity >= FALLBACK_THRESHOLD

    return verdict


def assign_article_to_story(
    article,
    embedding,
    checker=None,
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

    if should_attach(
        article,
        best_story,
        similarity,
        checker,
    ):

        attach_article_to_story(
            article_id=article["id"],
            story_id=best_story["id"],
            similarity=similarity,
        )

        refresh_story_embedding(
            best_story["id"]
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
