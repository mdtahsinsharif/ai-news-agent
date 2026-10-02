import os

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

from ai.text import clean_text

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-embedding-001"

# 768 keeps most of the full 3072-dimension quality at a
# quarter of the storage and comparison cost.
EMBEDDING_DIMENSIONS = 768

# CLUSTERING tunes the vectors for grouping similar texts,
# which is what story clustering does.
CONFIG = types.EmbedContentConfig(
    task_type="CLUSTERING",
    output_dimensionality=EMBEDDING_DIMENSIONS,
)


def normalize(values):
    """
    Gemini only normalizes full-size embeddings, so scale
    reduced ones to unit length to keep centroids unbiased.
    """

    vector = np.array(values, dtype=np.float32)

    norm = np.linalg.norm(vector)

    if norm == 0:
        return vector.tolist()

    return (vector / norm).tolist()

DESCRIPTION_CHARS = 500


def build_embedding_text(title, description):
    """
    Text embedded for an article: the title plus the start
    of the description, which adds context short headlines
    lack. Pipeline and backfill must both use this so their
    vectors are comparable.
    """

    description = clean_text(description)[:DESCRIPTION_CHARS]

    return f"{title}\n{description}".strip()


def generate_embedding(text):

    result = client.models.embed_content(
        model=MODEL,
        contents=text,
        config=CONFIG,
    )

    return normalize(result.embeddings[0].values)


def generate_embeddings(texts):

    result = client.models.embed_content(
        model=MODEL,
        contents=texts,
        config=CONFIG,
    )

    return [
        normalize(embedding.values)
        for embedding in result.embeddings
    ]


def is_daily_quota_error(error):
    """
    True when Gemini rejected the request because the
    daily quota is used up (it won't reset for hours).
    """

    return "PerDay" in str(error)
