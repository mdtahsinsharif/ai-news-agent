from ai.embeddings import generate_embedding


text = """
OpenAI announced a new artificial intelligence
model with improved reasoning capabilities.
"""


embedding = generate_embedding(text)


print(
    "Embedding generated"
)

print(
    "Dimensions:",
    len(embedding)
)

print(
    "First 10 values:",
    embedding[:10]
)