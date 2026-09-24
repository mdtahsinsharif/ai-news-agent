from ingestion.fetch_all import (
    fetch_all_sources,
)


articles = fetch_all_sources()


print(
    f"\nTotal articles: {len(articles)}"
)


for article in articles[:10]:

    print("\n----------------")

    print(
        "Source:",
        article["source"]
    )

    print(
        "Title:",
        article["title"]
    )

    print(
        "URL:",
        article["url"]
    )
