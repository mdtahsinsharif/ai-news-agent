
from database.repository import (
    find_similar_stories,
)

from ai.embeddings import generate_embedding


embedding = generate_embedding(
    "OpenAI releases another artificial intelligence model"
)

stories = find_similar_stories(
    embedding=embedding,
    limit=5,
)

print("\nSimilar stories:")

for story in stories:

    print(
        f"Story {story['id']}: "
        f"{story['headline']} "
        f"similarity={story['similarity']:.4f}"
    )
