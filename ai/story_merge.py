from database.repository import (
    get_merge_candidates,
    merge_stories,
    record_merge_rejection,
)

from ai.same_story import describe_story
from ai.story_embedding import refresh_story_embedding


# Above this, stories are merged without asking the LLM.
AUTO_MERGE_THRESHOLD = 0.85

# Pairs below this are never considered duplicates.
CANDIDATE_THRESHOLD = 0.75


def merge_duplicate_stories(checker=None):
    """
    Merge recent stories that turned out to cover the same
    event, e.g. because they started before their articles'
    clusters converged.
    """

    candidates = get_merge_candidates(
        min_similarity=CANDIDATE_THRESHOLD,
    )

    merged_away = set()
    merged = 0

    for pair in candidates:

        story_a = pair["story_a"]
        story_b = pair["story_b"]

        if story_a in merged_away or story_b in merged_away:
            continue

        if pair["similarity"] < AUTO_MERGE_THRESHOLD:

            if checker is None:
                continue

            verdict = checker.check(
                describe_story(story_a),
                describe_story(story_b),
            )

            # Couldn't ask; try again on the next run.
            if verdict is None:
                continue

            if not verdict:

                record_merge_rejection(
                    story_a,
                    story_b,
                )

                continue

        # Keep the larger story so its ID stays stable.
        if pair["count_a"] >= pair["count_b"]:
            keep, drop = story_a, story_b
        else:
            keep, drop = story_b, story_a

        merge_stories(
            keep_id=keep,
            drop_id=drop,
        )

        refresh_story_embedding(keep)

        merged_away.add(drop)
        merged += 1

        print(
            f"Merged story {drop} into {keep} "
            f"(similarity {pair['similarity']:.3f})"
        )

    return merged
