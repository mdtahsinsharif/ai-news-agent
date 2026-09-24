
import numpy as np

from database.repository import (
    get_story_article_embeddings,
    update_story_embedding,
)


def calculate_centroid(embeddings):
    """
    Calculate the normalized centroid of a collection
    of embeddings.
    """

    vectors = np.array(
        embeddings,
        dtype=np.float32,
    )

    centroid = vectors.mean(axis=0)

    # Normalize
    norm = np.linalg.norm(centroid)

    if norm == 0:
        return centroid.tolist()

    centroid = centroid / norm

    return centroid.tolist()


def refresh_story_embedding(story_id):
    """
    Recalculate the story embedding using all
    article embeddings belonging to the story.
    """

    embeddings = get_story_article_embeddings(
        story_id
    )

    if not embeddings:
        return None

    centroid = calculate_centroid(
        embeddings
    )

    update_story_embedding(
        story_id=story_id,
        embedding=centroid,
    )

    return centroid

