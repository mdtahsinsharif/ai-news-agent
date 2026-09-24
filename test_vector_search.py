from ai.embeddings import generate_embedding
from database.repository import search_similar_articles


query = (
    "OpenAI launches a new artificial "
    "intelligence model"
)

embedding = generate_embedding(query)

results = search_similar_articles(
    embedding,
    limit=10,
)

print(len(results))
for result in results:

    print(
        result["similarity"],
        result["source"],
        result["title"],
    )