import numpy as np
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_embedding(text):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values


def generate_embeddings(texts):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts
    )

    return [
        embedding.values
        for embedding in result.embeddings
    ]


def is_daily_quota_error(error):
    """
    True when Gemini rejected the request because the
    daily quota is used up (it won't reset for hours).
    """

    return "PerDay" in str(error)
